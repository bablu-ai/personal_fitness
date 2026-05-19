"""
Tests for the hybrid plan reviewer (MODIFY_WORKSHEET_PLAN_FINAL §8).

Pure-Python over dicts — no DB / FastAPI / fixtures needed.

Coverage per CLAUDE.md §8:
- Each Tier-A rule: a crafted bad task triggers exactly that fix + the
  correct log entry; a clean task is untouched.
- Each Tier-B code: produces the flag, does NOT mutate the task; a good
  task produces no flag.
- Boundaries: empty list, task with no task_id, all-junk list.
"""
import copy

from app.services.plan_reviewer import (
    apply_tier_a,
    generate_tier_b_flags,
    review_workbook_json,
)


def _task(**over):
    base = {
        "task_id": "t1",
        "pillar": "brief_today",
        "name": "Band row",
        "description": "Builds posture.",
        "schedule": "daily",
        "timing": None,
        "target_value": "2 rounds",
        "unit": None,
        "is_reference": False,
        "extra_metadata": {},
    }
    base.update(over)
    return base


# ── Tier A: instruction row ───────────────────────────────────────────────

def test_tier_a_drops_instruction_row():
    bad = _task(task_id="x", name="Quick note: log pain after each set")
    cleaned, removed, fixed = apply_tier_a([bad])
    assert cleaned == []
    assert removed == [{
        "reason": "instruction_row",
        "raw_name": "Quick note: log pain after each set",
        "task_id": "x",
    }]
    assert fixed == []


def test_tier_a_keeps_clean_task_untouched():
    clean = _task()
    original = copy.deepcopy(clean)
    cleaned, removed, fixed = apply_tier_a([clean])
    assert len(cleaned) == 1
    assert removed == [] and fixed == []
    assert clean == original  # input not mutated
    assert cleaned[0] == original


# ── Tier A: empty name ────────────────────────────────────────────────────

def test_tier_a_drops_empty_name():
    cleaned, removed, _ = apply_tier_a([_task(task_id="e", name="   ")])
    assert cleaned == []
    assert removed == [
        {"reason": "empty_name", "raw_name": "   ", "task_id": "e"}
    ]


def test_tier_a_drops_missing_name_key():
    cleaned, removed, _ = apply_tier_a([{"pillar": "supplements"}])
    assert cleaned == []
    assert removed[0]["reason"] == "empty_name"
    assert "task_id" not in removed[0]  # no task_id present


# ── Tier A: unparseable schedule → daily ──────────────────────────────────

def test_tier_a_normalizes_unparseable_schedule():
    cleaned, _, fixed = apply_tier_a([_task(schedule="whenever I feel like")])
    assert cleaned[0]["schedule"] == "daily"
    assert fixed == [{
        "task_id": "t1",
        "field": "schedule",
        "from": "whenever I feel like",
        "to": "daily",
    }]


def test_tier_a_keeps_parseable_schedules():
    # Only schedules the scheduler recognizes explicitly are left alone.
    # "8wk on / 2wk off" is NOT in the scheduler's literal recognized set
    # (it matches neither "on/off" nor "on / off" nor "cycle"), so it is
    # correctly treated as unparseable and normalized — covered below.
    for sched in ("daily", "weekly", "2x/wk", "Mon,Wed,Fri",
                  "as needed", None, "EOD", "8wk cycle on/off"):
        _, _, fixed = apply_tier_a([_task(schedule=sched)])
        assert fixed == [], f"{sched!r} should be parseable"


# ── Tier A: is_reference correction ───────────────────────────────────────

def test_tier_a_corrects_reference_false_to_true():
    cleaned, _, fixed = apply_tier_a([
        _task(pillar="nutrition", is_reference=False)
    ])
    assert cleaned[0]["is_reference"] is True
    assert fixed == [{
        "task_id": "t1", "field": "is_reference",
        "from": False, "to": True,
    }]


def test_tier_a_corrects_reference_true_to_false():
    cleaned, _, fixed = apply_tier_a([
        _task(pillar="supplements", is_reference=True)
    ])
    assert cleaned[0]["is_reference"] is False
    assert fixed[0]["to"] is False


def test_tier_a_leaves_ambiguous_pillar_reference_alone():
    _, _, fixed = apply_tier_a([
        _task(pillar="blood_markers", is_reference=True)
    ])
    assert fixed == []  # not a clear-cut pillar → no silent change


# ── Tier A: duplicate ─────────────────────────────────────────────────────

def test_tier_a_dedupes_exact_duplicate_keeps_first():
    a = _task(task_id="a", name="Walk", schedule="daily")
    b = _task(task_id="b", name="Walk", schedule="daily")
    cleaned, removed, _ = apply_tier_a([a, b])
    assert len(cleaned) == 1
    assert cleaned[0]["task_id"] == "a"
    dup = [r for r in removed if r["reason"] == "duplicate"]
    assert dup == [{
        "reason": "duplicate", "raw_name": "Walk",
        "pillar": "brief_today", "schedule": "daily", "task_id": "b",
    }]


def test_tier_a_different_schedule_not_duplicate():
    a = _task(task_id="a", name="Walk", schedule="daily")
    b = _task(task_id="b", name="Walk", schedule="weekly")
    cleaned, removed, _ = apply_tier_a([a, b])
    assert len(cleaned) == 2
    assert [r for r in removed if r["reason"] == "duplicate"] == []


# ── Tier B: name_is_dosage ────────────────────────────────────────────────

def test_tier_b_flags_name_is_dosage():
    t = _task(name="5 g", description="Creatine\nATP support")
    flags = generate_tier_b_flags([t])
    f = [x for x in flags if x["code"] == "name_is_dosage"]
    assert len(f) == 1
    assert f[0]["suggestion"] == "Creatine"
    assert f[0]["blocking"] is False
    assert f[0]["flag_id"] == "name_is_dosage:t1"


def test_tier_b_name_is_dosage_does_not_mutate():
    t = _task(name="500mg")
    snapshot = copy.deepcopy(t)
    generate_tier_b_flags([t])
    assert t == snapshot


def test_tier_b_good_name_no_dosage_flag():
    flags = generate_tier_b_flags([_task(name="Creatine monohydrate")])
    assert [f for f in flags if f["code"] == "name_is_dosage"] == []


# ── Tier B: missing_description ───────────────────────────────────────────

def test_tier_b_flags_missing_description():
    flags = generate_tier_b_flags([_task(description="")])
    f = [x for x in flags if x["code"] == "missing_description"]
    assert len(f) == 1 and f[0]["suggestion"] is None
    assert f[0]["blocking"] is False


def test_tier_b_reference_task_no_missing_description_flag():
    flags = generate_tier_b_flags([
        _task(pillar="nutrition", is_reference=True, description="")
    ])
    assert [f for f in flags if f["code"] == "missing_description"] == []


# ── Tier B: suspicious_reference ──────────────────────────────────────────

def test_tier_b_flags_suspicious_reference():
    flags = generate_tier_b_flags([
        _task(pillar="blood_markers", is_reference=False)
    ])
    f = [x for x in flags if x["code"] == "suspicious_reference"]
    assert len(f) == 1
    assert f[0]["suggestion"] is True  # toggled value
    assert f[0]["blocking"] is False


def test_tier_b_clearcut_pillar_no_suspicious_reference():
    flags = generate_tier_b_flags([_task(pillar="brief_today")])
    assert [f for f in flags if f["code"] == "suspicious_reference"] == []


# ── Tier B: empty_target ──────────────────────────────────────────────────

def test_tier_b_flags_empty_target():
    flags = generate_tier_b_flags([
        _task(pillar="supplements", target_value=None)
    ])
    f = [x for x in flags if x["code"] == "empty_target"]
    assert len(f) == 1 and f[0]["blocking"] is False


def test_tier_b_target_present_no_empty_target_flag():
    flags = generate_tier_b_flags([
        _task(pillar="supplements", target_value="5 g")
    ])
    assert [f for f in flags if f["code"] == "empty_target"] == []


# ── Tier B: pillar_mismatch (blocking) ────────────────────────────────────

def test_tier_b_flags_pillar_mismatch_blocking():
    flags = generate_tier_b_flags([_task(pillar="brief_todays")])
    f = [x for x in flags if x["code"] == "pillar_mismatch"]
    assert len(f) == 1
    assert f[0]["blocking"] is True
    assert f[0]["suggestion"] == "brief_today"  # nearest known pillar


def test_tier_b_known_pillar_no_mismatch():
    for p in ("brief_today", "supplements", "nutrition",
              "sleep_recovery", "blood_markers"):
        flags = generate_tier_b_flags([_task(pillar=p)])
        assert [f for f in flags if f["code"] == "pillar_mismatch"] == []


def test_tier_b_flag_id_falls_back_to_index_without_task_id():
    t = _task(name="5 g")
    t.pop("task_id")
    flags = generate_tier_b_flags([t])
    f = [x for x in flags if x["code"] == "name_is_dosage"][0]
    assert f["flag_id"] == "name_is_dosage:idx:0"


# ── Boundaries ────────────────────────────────────────────────────────────

def test_empty_task_list():
    cleaned, removed, fixed = apply_tier_a([])
    assert (cleaned, removed, fixed) == ([], [], [])
    assert generate_tier_b_flags([]) == []


def test_all_junk_list_fully_removed():
    junk = [
        _task(name="Quick note: move slow on the eccentric"),
        _task(name="   "),
        {"name": "log pain after each set and stop if sharp"},
    ]
    cleaned, removed, _ = apply_tier_a(junk)
    assert cleaned == []
    assert len(removed) == 3


def test_tier_a_only_reuses_shared_instruction_regex_intent():
    """Conservative-by-design: a phrase the shared _INSTRUCTION_RE does NOT
    match (e.g. "If behind schedule, ...") is NOT silently dropped — it is
    kept and surfaced for human review instead, keeping one source of truth
    for instruction detection (plan_ingest._INSTRUCTION_RE)."""
    t = _task(name="If behind schedule, drop the last round")
    cleaned, removed, _ = apply_tier_a([t])
    assert len(cleaned) == 1
    assert [r for r in removed if r["reason"] == "instruction_row"] == []


# ── Public entry point ────────────────────────────────────────────────────

def test_review_workbook_json_does_not_mutate_input():
    wb = {
        "tasks": [
            _task(name="Quick note: log pain"),       # dropped
            _task(task_id="k", pillar="nutrition", is_reference=False),
        ],
        "review": {"auto_removed": [], "flags": [],
                   "advisor_notes": ["pre-existing"]},
    }
    snapshot = copy.deepcopy(wb)
    out = review_workbook_json(wb)

    assert wb == snapshot  # input untouched
    assert out is not wb
    assert len(out["tasks"]) == 1
    assert out["tasks"][0]["is_reference"] is True  # Tier-A applied
    assert len(out["review"]["auto_removed"]) == 1
    assert "agent_fixed" in out["review"]
    assert out["review"]["advisor_notes"] == ["pre-existing"]


def test_review_workbook_json_handles_missing_tasks_key():
    out = review_workbook_json({})
    assert out["tasks"] == []
    assert out["review"] == {
        "auto_removed": [], "agent_fixed": [],
        "flags": [], "advisor_notes": [],
    }


def test_review_workbook_json_tier_b_sees_only_cleaned_tasks():
    wb = {"tasks": [
        _task(name="Quick note: stop if pain", pillar="brief_todays"),
    ]}
    out = review_workbook_json(wb)
    # the junk row was dropped by Tier-A, so no Tier-B flag for it
    assert out["tasks"] == []
    assert out["review"]["flags"] == []
