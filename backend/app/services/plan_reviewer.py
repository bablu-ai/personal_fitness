"""
Hybrid backend plan reviewer (MODIFY_WORKSHEET_PLAN_FINAL §8).

Pure Python, no FastAPI / DB imports. Operates only on the canonical
``workbook_json`` dict (shape produced by ``_plan_to_json`` /
``ingest_from_workbook_json``: top-level ``tasks: list[dict]`` plus a
``review`` envelope ``{"auto_removed": [], "flags": [], "advisor_notes": []}``).

Two tiers:

* **Tier A — silent fixes** (deterministic, low-risk). Applied during ingest.
  Drops obvious junk rows and applies safe normalizations, logging every
  action to ``review.auto_removed`` / ``review.agent_fixed``. Never asks
  the user.
* **Tier B — flag + suggest** (NEVER mutates a task). Appends advisory
  flags to ``review.flags`` for human approval. CONSTITUTION LLM06: the
  agent only proposes — the apply / dismiss endpoints belong to
  subagent #5.

LLM use is **out of scope for v1** — every Tier-A and Tier-B rule here is a
small, pure, deterministic function so it is independently testable and
cannot delete or activate anything.

──────────────────────────────────────────────────────────────────────────
Schedule-parseability contract (read by subagent #5)
──────────────────────────────────────────────────────────────────────────
``scheduler._is_scheduled_today`` deliberately returns ``True`` for *unknown*
schedules ("don't silently drop tasks", scheduler.py line 79), so it CANNOT
be used to detect an unparseable schedule. ``_is_schedule_parseable`` below
re-implements the *positive* recognition set used by the scheduler:

    None / "" / whitespace            → parseable (scheduler defaults to daily)
    daily / every day / everyday /
        all days                      → parseable
    weekly                            → parseable
    weekdays / workdays / weekends    → parseable
    eod / alternate day / every other
        day / every 2 days families   → parseable
    2x/wk, 3x/wk (× or x, optional
        slash/spaces)                 → parseable
    cycle / on-off / on / off         → parseable
    comma-separated WEEKDAY_MAP names → parseable
    any _SKIP_PATTERNS member         → parseable (skip is a valid intent)
    anything else                     → NOT parseable → Tier-A normalizes
                                          it to "daily" and logs agent_fixed.

──────────────────────────────────────────────────────────────────────────
flag_id scheme (read by subagent #5 for apply / dismiss endpoints)
──────────────────────────────────────────────────────────────────────────
Every Tier-B flag carries a deterministic, re-run-stable ``flag_id``:

    flag_id = f"{code}:{task_id}"                 (task has a task_id)
    flag_id = f"{code}:idx:{index}"               (legacy task, no task_id)

No UUIDs — the same plan JSON reviewed twice yields identical flag ids, so
an apply / dismiss request stays addressable across reloads. Subagent #5
can split on the first ``:`` to recover ``code`` and route the rest.
"""
from __future__ import annotations

import copy
import re
from typing import Any

from app.constants import REFERENCE_PILLARS
from app.services.plan_ingest import _INSTRUCTION_RE
from app.services.scheduler import WEEKDAY_MAP, _SKIP_PATTERNS

# ── Known classifications ────────────────────────────────────────────────

# Pillars that must be is_reference=True.
_REFERENCE_PILLARS: frozenset[str] = frozenset(REFERENCE_PILLARS)

# Pillars that are actionable daily tasks → must be is_reference=False.
_ACTIONABLE_PILLARS: frozenset[str] = frozenset({"brief_today", "supplements"})

# Every pillar the codebase legitimately produces (reference + actionable +
# screening sheets parsed into the Screening table).
_KNOWN_PILLARS: frozenset[str] = (
    _REFERENCE_PILLARS
    | _ACTIONABLE_PILLARS
    | frozenset({"blood_markers", "screenings_safety"})
)

# Pillars for which a missing target_value is worth flagging.
_TARGET_REQUIRED_PILLARS: frozenset[str] = frozenset({"brief_today", "supplements"})

# name looks like a bare dosage: optional leading number/×/unit punctuation
# then a measurement unit token. e.g. "5 g", "500mg", "30 min", "12 reps".
_DOSAGE_NAME_RE = re.compile(r"^[\d.,×x/–\- ]*(g|mg|ml|min|sec|reps?)\b", re.I)

# 2x/wk and 3x/wk recognizers (mirror scheduler regexes).
_2X_RE = re.compile(r"2\s*[x×]\s*/?\s*w(ee)?k")
_3X_RE = re.compile(r"3\s*[x×]\s*/?\s*w(ee)?k")
_PAREN_RE = re.compile(r"\(.*?\)")


# ── Schedule parseability (see module docstring contract) ─────────────────

def _is_schedule_parseable(schedule: str | None) -> bool:
    """True iff *schedule* is one the scheduler recognizes explicitly.

    Mirrors the positive branches of ``scheduler._is_scheduled_today``;
    unlike that function this does NOT default unknown values to a truthy
    result — an unrecognized schedule returns ``False`` so Tier-A can
    normalize it to ``"daily"``.
    """
    if schedule is None:
        return True
    s = schedule.strip().lower()
    if not s:
        return True

    s_clean = _PAREN_RE.sub("", s).strip()

    if s_clean in _SKIP_PATTERNS or any(p in s_clean for p in _SKIP_PATTERNS):
        return True
    if s_clean in ("daily", "every day", "everyday", "all days"):
        return True
    if s_clean == "weekly":
        return True
    if s_clean in ("weekdays", "workdays", "weekends"):
        return True
    if s_clean in (
        "eod", "alternate day", "alternating day",
        "every other day", "every 2 days",
    ):
        return True
    if _2X_RE.search(s_clean) or _3X_RE.search(s_clean):
        return True
    if "cycle" in s_clean or "on/off" in s_clean or "on / off" in s_clean:
        return True
    parts = [p.strip() for p in s_clean.split(",")]
    if any(p in WEEKDAY_MAP for p in parts):
        return True
    return False


# ── Small per-rule predicates (each independently testable) ───────────────

def _name_of(task: dict[str, Any]) -> str:
    name = task.get("name")
    return name if isinstance(name, str) else ""


def _is_instruction_row(task: dict[str, Any]) -> bool:
    """name reads like an instruction / note, not a real task."""
    name = _name_of(task)
    return bool(name.strip()) and bool(_INSTRUCTION_RE.search(name))


def _is_empty_name(task: dict[str, Any]) -> bool:
    return not _name_of(task).strip()


def _is_reference_wrong(task: dict[str, Any]) -> bool:
    """True when is_reference clearly contradicts a known pillar rule."""
    pillar = task.get("pillar")
    is_ref = bool(task.get("is_reference", False))
    if pillar in _REFERENCE_PILLARS and not is_ref:
        return True
    if pillar in _ACTIONABLE_PILLARS and is_ref:
        return True
    return False


def _correct_is_reference(task: dict[str, Any]) -> bool:
    """The correct is_reference value for a clear-cut pillar."""
    return task.get("pillar") in _REFERENCE_PILLARS


def _dup_key(task: dict[str, Any]) -> tuple[Any, Any, Any]:
    return (task.get("pillar"), task.get("name"), task.get("schedule"))


# ── Tier A — silent deterministic fixes ───────────────────────────────────

def apply_tier_a(
    tasks: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    """Apply silent, low-risk fixes.

    Returns ``(cleaned_tasks, auto_removed, agent_fixed)``. ``tasks`` is not
    mutated — task dicts that survive are shallow-copied before any field
    change so callers' input stays intact.

    Order: instruction-row / empty-name drops → schedule normalize →
    is_reference correction → exact-duplicate dedupe. Drop reasons are
    mutually exclusive (instruction row is checked before empty name).
    """
    cleaned: list[dict[str, Any]] = []
    auto_removed: list[dict[str, Any]] = []
    agent_fixed: list[dict[str, Any]] = []

    for task in tasks:
        if _is_instruction_row(task):
            entry: dict[str, Any] = {
                "reason": "instruction_row",
                "raw_name": _name_of(task),
            }
            if task.get("task_id") is not None:
                entry["task_id"] = task.get("task_id")
            auto_removed.append(entry)
            continue

        if _is_empty_name(task):
            entry = {"reason": "empty_name", "raw_name": _name_of(task)}
            if task.get("task_id") is not None:
                entry["task_id"] = task.get("task_id")
            auto_removed.append(entry)
            continue

        fixed = dict(task)  # shallow copy — never mutate the input dict

        if not _is_schedule_parseable(fixed.get("schedule")):
            agent_fixed.append({
                "task_id": fixed.get("task_id"),
                "field": "schedule",
                "from": fixed.get("schedule"),
                "to": "daily",
            })
            fixed["schedule"] = "daily"

        if _is_reference_wrong(fixed):
            correct = _correct_is_reference(fixed)
            agent_fixed.append({
                "task_id": fixed.get("task_id"),
                "field": "is_reference",
                "from": bool(fixed.get("is_reference", False)),
                "to": correct,
            })
            fixed["is_reference"] = correct

        cleaned.append(fixed)

    # Exact-duplicate (pillar, name, schedule): keep first, drop the rest.
    deduped: list[dict[str, Any]] = []
    seen: set[tuple[Any, Any, Any]] = set()
    for task in cleaned:
        key = _dup_key(task)
        if key in seen:
            entry = {
                "reason": "duplicate",
                "raw_name": _name_of(task),
                "pillar": task.get("pillar"),
                "schedule": task.get("schedule"),
            }
            if task.get("task_id") is not None:
                entry["task_id"] = task.get("task_id")
            auto_removed.append(entry)
            continue
        seen.add(key)
        deduped.append(task)

    return deduped, auto_removed, agent_fixed


# ── Tier B — flag + suggest (never mutates) ───────────────────────────────

def _flag_id(code: str, task: dict[str, Any], index: int) -> str:
    """Deterministic, re-run-stable flag identifier (see module docstring)."""
    task_id = task.get("task_id")
    if task_id:
        return f"{code}:{task_id}"
    return f"{code}:idx:{index}"


def _suggest_name_from(task: dict[str, Any]) -> str | None:
    """Derive a human name suggestion from description / source_key."""
    desc = task.get("description")
    if isinstance(desc, str):
        first = desc.strip().splitlines()[0].strip() if desc.strip() else ""
        if first:
            return first
    src = task.get("source_key")
    if isinstance(src, str) and src.strip():
        return src.strip()
    return None


def _nearest_known_pillar(pillar: Any) -> str | None:
    """Closest known pillar by simple substring / prefix overlap."""
    if not isinstance(pillar, str) or not pillar.strip():
        return None
    p = pillar.strip().lower()
    for known in _KNOWN_PILLARS:
        if p in known or known in p:
            return known
    best: str | None = None
    best_len = 0
    for known in _KNOWN_PILLARS:
        common = len(set(p) & set(known))
        if common > best_len:
            best_len, best = common, known
    return best


def generate_tier_b_flags(
    tasks: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Produce advisory flags. NEVER mutates *tasks*.

    Each flag: ``{flag_id, task_id, code, message, suggestion, blocking}``.
    Only ``pillar_mismatch`` is blocking (it makes the row unschedulable);
    every other code is advisory (blocking=False).
    """
    flags: list[dict[str, Any]] = []

    for index, task in enumerate(tasks):
        task_id = task.get("task_id")
        pillar = task.get("pillar")
        name = _name_of(task)
        is_ref = bool(task.get("is_reference", False))
        description = task.get("description")
        target = task.get("target_value")

        # pillar_mismatch — blocking (unknown pillar breaks projection)
        if pillar not in _KNOWN_PILLARS:
            flags.append({
                "flag_id": _flag_id("pillar_mismatch", task, index),
                "task_id": task_id,
                "code": "pillar_mismatch",
                "message": f"Pillar {pillar!r} is not a known sheet pillar.",
                "suggestion": _nearest_known_pillar(pillar),
                "blocking": True,
            })

        # name_is_dosage — name looks like a bare measurement
        if name.strip() and _DOSAGE_NAME_RE.match(name.strip()):
            flags.append({
                "flag_id": _flag_id("name_is_dosage", task, index),
                "task_id": task_id,
                "code": "name_is_dosage",
                "message": (
                    f"Name {name!r} looks like a dosage, not a task name."
                ),
                "suggestion": _suggest_name_from(task),
                "blocking": False,
            })

        # missing_description — actionable task with no description
        if not is_ref and not (
            isinstance(description, str) and description.strip()
        ):
            flags.append({
                "flag_id": _flag_id("missing_description", task, index),
                "task_id": task_id,
                "code": "missing_description",
                "message": "Actionable task has no description.",
                "suggestion": None,
                "blocking": False,
            })

        # suspicious_reference — is_reference ambiguous (pillar not clear-cut)
        if pillar not in _REFERENCE_PILLARS and pillar not in _ACTIONABLE_PILLARS:
            flags.append({
                "flag_id": _flag_id("suspicious_reference", task, index),
                "task_id": task_id,
                "code": "suspicious_reference",
                "message": (
                    f"is_reference={is_ref} is ambiguous for pillar "
                    f"{pillar!r}."
                ),
                "suggestion": not is_ref,
                "blocking": False,
            })

        # empty_target — brief_today / supplement with no target_value
        if pillar in _TARGET_REQUIRED_PILLARS and not (
            isinstance(target, str) and target.strip()
        ):
            flags.append({
                "flag_id": _flag_id("empty_target", task, index),
                "task_id": task_id,
                "code": "empty_target",
                "message": (
                    f"{pillar} task has no target_value."
                ),
                "suggestion": None,
                "blocking": False,
            })

    return flags


# ── Public entry point ────────────────────────────────────────────────────

def review_workbook_json(workbook_json: dict[str, Any]) -> dict[str, Any]:
    """Run Tier-A then Tier-B over *workbook_json*; return a NEW dict.

    The input is deep-copied first so the caller's object is never mutated.
    The returned dict has cleaned ``tasks`` and a fully populated ``review``
    envelope:

        {"auto_removed": [...], "agent_fixed": [...],
         "flags": [...], "advisor_notes": [...]}

    Tier-B reads the *cleaned* tasks (post Tier-A) so flags reflect the
    rows the user will actually see, and is read-only over them.
    """
    out = copy.deepcopy(workbook_json) if workbook_json else {}

    raw_tasks = out.get("tasks", [])
    if not isinstance(raw_tasks, list):
        raw_tasks = []

    cleaned, auto_removed, agent_fixed = apply_tier_a(raw_tasks)
    flags = generate_tier_b_flags(cleaned)

    existing_review = out.get("review")
    advisor_notes: list[Any] = []
    if isinstance(existing_review, dict):
        notes = existing_review.get("advisor_notes")
        if isinstance(notes, list):
            advisor_notes = notes

    out["tasks"] = cleaned
    out["review"] = {
        "auto_removed": auto_removed,
        "agent_fixed": agent_fixed,
        "flags": flags,
        "advisor_notes": advisor_notes,
    }
    return out
