# Changelog — Personal Longevity App

## Commit `0e9a9e8` — Plan Editor, xlsx Rebuild, Auth, Questionnaire, Todo Overrides

**80 files changed · 10,956 insertions · 130 deletions**

---

## Overview

This release adds the full task review/edit lifecycle for ingested plans, a downloadable xlsx export, stub auth, an interactive questionnaire flow, and per-day todo overrides.

---

## Backend

### New: Plan Editor API (`/api/plan/{id}/...`)

| Endpoint | Method | Description |
|---|---|---|
| `/api/plan/{id}/review` | GET | Full plan state: tasks grouped by pillar, rotation days, screenings, live Tier-B flags |
| `/api/plan/{id}/tasks` | POST | Add a new task; concurrency-guarded by `json_version` |
| `/api/plan/{id}/tasks/{task_id}` | PUT | Edit an existing task |
| `/api/plan/{id}/tasks/{task_id}` | DELETE | Remove a task (past history preserved via tombstone) |
| `/api/plan/{id}/rotation/{day}` | PUT | Edit a rotation day |
| `/api/plan/{id}/screenings/{id}` | PUT | Edit a screening |
| `/api/plan/{id}/flags/{flag_id}/apply` | POST | Apply a reviewer flag's suggestion |
| `/api/plan/{id}/flags/{flag_id}/dismiss` | POST | Dismiss a flag without applying it |
| `/api/plan/{id}/activate` | POST | Promote plan from `draft` → `active`; blocks on unresolved blocking flags |
| `/api/plan/{id}/download.xlsx` | GET | Download plan as Excel workbook |

**Files:** `backend/app/routers/plan_edit.py`, `backend/app/schemas/plan_edit.py`, `backend/app/services/plan_editor.py`

---

### New: History-Safe Re-projection (`plan_reproject.py`)

Every task edit, deletion, or flag apply calls `reproject_plan_from_json()` which enforces five guarantees:

1. **Past is immutable** — `DailyTodo` rows with `date < today` are never deleted.
2. **Future is regenerated** — Only `date >= today` rows are dropped and re-prefilled (next 30 days).
3. **Today preserved-if-completed** — A completed today-row survives and stays linked to its task.
4. **Stable task identity** — Old↔new tasks matched by `task_id` = `TaskTemplate.id`; a rename keeps full history.
5. **Atomic** — The entire operation is one transaction; any error rolls back to the prior state.

**Tombstone pattern:** Deleted tasks that still have history rows are kept as DB-only tombstones (excluded from future todos and from plan_json on the next edit).

**File:** `backend/app/services/plan_reproject.py`

---

### New: Hybrid Plan Reviewer (`plan_reviewer.py`)

Two tiers of quality checks run on every `GET /review`:

**Tier A — Silent fixes (applied during ingest, never shown to user):**
- Instruction/note rows dropped automatically
- Empty-name rows dropped
- Unparseable schedules normalized to `"daily"`
- `is_reference` corrected for known pillars
- Exact duplicates deduplicated

**Tier B — Flag + suggest (never auto-applied, human approval required):**

| Code | Blocking | Description |
|---|---|---|
| `pillar_mismatch` | Yes | Unknown pillar — row cannot be scheduled |
| `name_is_dosage` | No | Name looks like a bare measurement (e.g. "500mg") |
| `missing_description` | No | Actionable task has no description |
| `suspicious_reference` | No | `is_reference` is ambiguous for this pillar |
| `empty_target` | No | `brief_today`/`supplements` task has no target_value |

Dismissed flags persist in `plan_json["review"]["dismissed_flag_ids"]` so they do not reappear on the next GET.

**File:** `backend/app/services/plan_reviewer.py`

---

### New: xlsx Rebuild (`workbook_to_xlsx.py`)

Generates a downloadable `.xlsx` from `plan_json` using the project template as a base. Each sheet writer is fault-isolated — one bad sheet never aborts the download.

Sheets written:
- `01_Personal_Settings`
- `02_Brief_Today`
- `09_Supplements`
- `10_Blood_Markers`
- `11_Screenings_Safety`
- `05_30Day_Rotation`

**File:** `backend/app/services/workbook_to_xlsx.py`

---

### New: Draft/Active Plan Lifecycle

- **Ingested plans** are now created with `status='draft'`, `is_active=False` — invisible to the scheduler until explicitly approved.
- **Activation** (`POST /activate`) checks for blocking flags, archives any prior active plan, flips `is_active=True`, and reprojects future todos.
- **Concurrency guard** — `Plan.json_version` is bumped on every `plan_json` write. Stale-base edits are rejected with `409`.

**Modified:** `backend/app/services/plan_ingest.py`

---

### New: Per-Day Todo Overrides

`DailyTodo.override_json` stores a per-day overlay `{"name"?, "target_value"?, "hidden"?}` applied at the response layer — the template is never mutated.

- `hidden: true` → todo excluded from day view (DB row preserved for history)
- `name` / `target_value` → override template values for this date only
- PATCH merges into existing overlay; send `null` to clear

**Modified:** `backend/app/routers/todos.py`, `backend/app/schemas/todo.py`

---

### New: Auth (Phase 1 Stub)

Basic email/password registration and login with bcrypt hashing and JWT tokens. Marked `TODO[SECURITY]` for Phase 2 hardening (MFA, refresh rotation, session revocation).

**Files:** `backend/app/routers/auth.py`, `backend/app/schemas/auth.py`, `backend/app/services/auth_service.py`

---

### New: Questionnaire Flow

Multi-section intake questionnaire (40 questions) that generates a personalized workbook JSON via LLM. Sessions are persistent so users can resume mid-flow.

**Files:** `backend/app/routers/questionnaire.py`, `backend/app/schemas/questionnaire.py`, `backend/app/services/questionnaire_generator.py`

---

### Database Migrations

| Migration | Changes |
|---|---|
| `b1c2d3e4f5a6` | `users`, `questionnaire_sessions`, `questionnaire_answers`, `generated_workbooks` tables |
| `c2d3e4f5a6b7` | `plans.status`, `plans.json_version`, `task_templates.origin`, `daily_todos.override_json` |

---

### Infrastructure Fixes

- **SQLite NullPool** — `database.py` now uses `NullPool` for SQLite so Alembic DDL (`batch_alter_table`) can acquire an exclusive lock without being blocked by the application's connection pool.
- **`TESTING` guard** — `app/main.py` skips `_run_migrations()` when `TESTING=1`, preventing test collection from touching the real `longevity.db`.

---

## Tests

**185 tests — all passing, stable across two runs.**

| Test file | Tests | What it covers |
|---|---|---|
| `test_plan_editor.py` | 25 | All 10 plan-edit endpoints: 200/201/204, 409 stale, 404, blocking flag gate, archive prior plan, tombstone invariant |
| `test_plan_reproject.py` | ~40 | History-safety rules, tombstone, today-completed preservation, rotation/screening rebuild |
| `test_plan_reviewer.py` | ~35 | All Tier-A and Tier-B rules, dismissed flag persistence, flag_id stability |
| `test_workbook_to_xlsx.py` | ~30 | Sheet helpers (normalize_pillar, find_header_row, col_map, clear_block) + integration |
| `test_todos_override.py` | ~25 | Override merge semantics, hidden filter, PATCH behavior |
| `test_plan_ingest.py` | ~20 | Ingest pipeline end-to-end, plan_json serialization |
| `test_auth.py` | ~15 | Register, login, duplicate email, bad credentials |
| `test_questionnaire.py` | ~20 | Session create, answer, resume, generation trigger |
| `test_scheduler.py` | (updated) | Schedule parsing extended for new patterns |
| `conftest.py` | — | Shared in-memory SQLite fixtures with StaticPool isolation |

Negative-verification confirmed: flipping the version guard condition caused stale-version tests to fail immediately.

---

## Frontend

### New: Auth Flow
- `LoginPage.tsx`, `RegisterPage.tsx` — email/password forms
- `AuthContext.tsx` — JWT stored in memory; React context for `useAuth()`
- `ProtectedRoute.tsx` — redirect to login if unauthenticated
- `api/auth.ts` — typed API calls for register/login

### New: Questionnaire Feature (`src/features/questionnaire/`)
Full multi-screen flow:
- `SessionListPage` — list past sessions, start new
- `QuestionnairePage` — orchestrates all screens
- `SectionOverviewScreen` — section intro with progress
- `QuestionScreen` — renders any question type
- `ReviewScreen` — review answers before submitting
- `GenerationScreen` — spinner while workbook is generated

Input components: `TextInput`, `NumberInput`, `TimeInput`, `SingleChoiceInput`, `MultiChoiceInput`, `ConditionalInput`

Hook: `useQuestionnaire.ts` — state machine for session lifecycle (TanStack Query backed)

### Updated: Todos
- `TodoItem`, `TaskDetailDrawer`, `BriefTodayTimeline`, `TodayPage`, `RotationWeekView` — refined UI and override support
- `useTodos.ts` — extended for override PATCH calls

### Updated: Dashboard & Agent
- `DashboardPage`, `BenefitScoreCards` — UI refinements
- `AgentChat.tsx` — improved conversation UX

### Tests moved to `frontend/tests/`
- `BriefTodayTimeline.test.tsx`, `TaskDetailDrawer.test.tsx`, `TodoItem.test.tsx`
- New: `AgentChat.test.tsx`, `questionnaire/` test suite (5 files, ~700 lines)
