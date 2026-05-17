# Longevity Daily — Backend

FastAPI backend for the Longevity Daily-Action app. Ingests Excel or JSON plans via an AI pipeline, tracks daily completions, calculates evidence-based health benefit scores, and proxies an LLM coaching agent that knows your full plan.

## Tech Stack

| Layer | Choice |
|---|---|
| Framework | Python 3.11+ + FastAPI |
| Database | SQLite (POC) → PostgreSQL (Phase 2) |
| ORM | SQLAlchemy 2.0 (mapped_column style) |
| Migrations | Alembic (auto-runs on startup) |
| Excel parsing | openpyxl |
| AI ingest | LangChain + Claude / GPT-4o (structured output) |
| LLM Coach | LangChain + Anthropic / OpenAI |
| Testing | pytest |
| Linting | Ruff + mypy |

## Project Structure

```
backend/
├── app/
│   ├── main.py                  # FastAPI app, CORS, Alembic auto-migration, router wiring
│   ├── constants.py             # COLUMN_HINTS, SKIP_SHEETS, REFERENCE_PILLARS
│   ├── db/
│   │   ├── database.py          # SQLAlchemy engine + session
│   │   └── models.py            # Plan, TaskTemplate, DailyTodo, RotationDay,
│   │                            #   RotationCompletion, Screening, ScreeningRecord
│   ├── schemas/                 # Pydantic request/response models
│   ├── routers/
│   │   ├── upload.py            # POST /api/upload  (classic column-mapped parser)
│   │   ├── todos.py             # GET/PATCH /api/todos, GET /api/tasks/{id}/detail
│   │   ├── rotation.py          # GET/PATCH /api/rotation/*
│   │   ├── screenings.py        # GET/POST /api/screenings/*
│   │   ├── dashboard.py         # GET /api/dashboard/*
│   │   ├── benefits.py          # GET /api/benefits/*
│   │   └── agent.py             # POST /api/agent/chat, POST /api/agent/ingest
│   └── services/
│       ├── excel_parser.py      # Classic sheet→pillar parser (flexible column hints)
│       ├── plan_ingest.py       # AI ingest pipeline: extract→Claude→save→prefill todos
│       ├── scheduler.py         # Daily TODO generation + schedule parsing
│       ├── benefit_scorer.py    # Reads benefit_config.json, calculates scores
│       └── llm_agent.py        # LangChain coach — uses plan_json + today's progress
├── alembic/                     # Migration scripts (auto-generated)
├── tests/                       # pytest — all services + routes
├── benefit_config.json          # Benefit weights — edit to change scoring, no code needed
├── requirements.txt
└── .env.example
```

## Prerequisites

- Python 3.11+
- pip

## Setup & Run

```bash
# 1. Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # macOS / Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Create your .env file
cp .env.example .env
# Set ANTHROPIC_API_KEY or OPENAI_API_KEY to enable AI features

# 4. Start the server  (Alembic migrations run automatically on startup)
uvicorn app.main:app --reload
```

API: **http://localhost:8000** | Swagger: **http://localhost:8000/docs**

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./longevity.db` | SQLAlchemy DB URL |
| `CORS_ORIGINS` | `http://localhost:5173` | Allowed frontend origins |
| `LLM_PROVIDER` | `anthropic` | `anthropic` or `openai` |
| `LLM_MODEL` | `claude-haiku-4-5-20251001` | Model for the chat agent |
| `LLM_INGEST_MODEL` | `claude-sonnet-4-6` | Model for AI plan ingest (needs more capability) |
| `ANTHROPIC_API_KEY` | _(unset)_ | Required for AI ingest + coach |
| `OPENAI_API_KEY` | _(unset)_ | Alternative LLM provider |

Both AI ingest and the chat coach degrade gracefully when no API key is set.

## API Endpoints

### Plan ingestion
| Method | Path | Description |
|---|---|---|
| `POST` | `/api/upload` | Classic upload — column-mapped `.xlsx` parser |
| `POST` | `/api/agent/ingest` | **AI ingest** — accepts `.xlsx` or `.json`, Claude normalizes |

### Todos
| Method | Path | Description |
|---|---|---|
| `GET` | `/api/todos/today` | Today's task list (auto-generated if not pre-filled) |
| `GET` | `/api/todos/{date}` | Tasks for any date |
| `PATCH` | `/api/todos/{id}` | Mark complete/incomplete, log actual value |
| `GET` | `/api/todos/{date}/summary` | Completion summary by pillar |
| `GET` | `/api/tasks/{id}/detail` | Full task detail + related exercises |
| `GET` | `/api/reference` | Reference items (nutrition, sleep, exercise library) |

### 30-day rotation
| Method | Path | Description |
|---|---|---|
| `GET` | `/api/rotation/today` | Today's rotation day |
| `GET` | `/api/rotation/week` | Mon–Sun grid for a week |
| `PATCH` | `/api/rotation/start` | Set rotation start date |
| `PATCH` | `/api/rotation/complete` | Mark a rotation day done |

### Screenings
| Method | Path | Description |
|---|---|---|
| `GET` | `/api/screenings` | All screenings |
| `GET` | `/api/screenings/due` | Overdue or due-soon screenings |
| `POST` | `/api/screenings/{id}/done` | Record a screening completion |

### Analytics & AI
| Method | Path | Description |
|---|---|---|
| `GET` | `/api/dashboard/daily` | Daily completion rows (last N days) |
| `GET` | `/api/dashboard/weekly` | Weekly rollup |
| `GET` | `/api/dashboard/monthly` | Monthly rollup |
| `GET` | `/api/benefits/today` | Health benefit scores for today |
| `POST` | `/api/agent/chat` | Chat with the LLM coach |
| `GET` | `/api/health` | Health check |

## How to Update Your Plan

**Recommended workflow (AI Ingest):**

1. Edit your spreadsheet — add tasks, rename columns, restructure sheets freely
2. Open the app → Upload tab → **AI Ingest**
3. Drop the new `.xlsx` (or export to `.json` and drop that)
4. Claude reads every sheet regardless of column names, normalizes the data, and pre-generates 30 days of todos
5. No code changes needed — column names and sheet structure do not matter

**Classic Upload (fallback):**

Uses rigid column-name hints. Works well when column names match the expected patterns. Faster (no LLM call) but breaks when columns are renamed.

## AI Ingest — How It Works

```
.xlsx or .json
    → extract_xlsx_text()     # openpyxl: convert every sheet to readable text
    → normalize_with_claude() # Claude returns IngestedPlan (structured JSON)
    → _wipe_user_data()       # delete old plan data
    → save Plan + TaskTemplates + RotationDays + Screenings
    → plan_json stored on Plan row (source of truth for agent chat)
    → prefill_todos()         # generate DailyTodo rows for next 30 days
```

The `plan_json` column on the Plan table stores Claude's full normalized JSON. The chat agent reads this on every message so it can answer questions about supplements, rotation days, exercise instructions, and screenings.

## Excel / Workbook Format

The AI ingest handles any column layout. For the classic upload, column hints are defined in `constants.py` — add new hint strings there if your headers change.

**Sheets automatically handled:**
- Any sheet → pillar (numeric prefix stripped, e.g. `09_Supplements` → `supplements`)
- `30day_rotation` sheet → `rotation_days` table (v3 and v4 layouts both supported)
- `blood_markers`, `screenings_safety` → `screenings` table
- `nutrition`, `sleep_recovery`, `cognitive_social`, `exercise_library` → reference items only (not daily todos)
- `readme`, `dashboard`, `17_time_audit`, `18_demo_link_guide`, etc. → skipped

## Database Migrations

Alembic runs automatically on every server start — no manual steps needed.

To generate a migration after changing `models.py`:

```bash
alembic revision --autogenerate -m "describe what changed"
alembic upgrade head
```

## Benefit Scoring

Weights live in `benefit_config.json` — not hardcoded. Edit that file to:
- Add new health outcomes
- Adjust pillar weights
- Rename outcomes or add icons

No code changes needed.

## Running Tests

```bash
pytest -q                  # Test Pass A
pytest -q                  # Test Pass B (run twice — check for order dependence)
ruff check .               # Lint
```

## Phase Roadmap

| Phase | Status | Notes |
|---|---|---|
| 1 — POC | **Current** | SQLite, single user, stub auth, AI ingest |
| 2 — Multi-user | Planned | PostgreSQL, OAuth (Google/Facebook), per-user data isolation |
| 3 — Reports | Planned | PDF export, trend charts, share links |
