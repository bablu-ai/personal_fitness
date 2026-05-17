# Longevity Daily — Frontend

React frontend for the Longevity Daily-Action app. Displays your daily health tasks across all pillars, lets you check them off, shows your 30-day exercise rotation, tracks health screenings, and lets you chat with an AI coach that knows your full plan.

## Tech Stack

| Layer | Choice |
|---|---|
| Framework | React 18 + Vite |
| Language | TypeScript (strict) |
| Styling | Tailwind CSS + Shadcn/ui |
| State — Server | TanStack Query v5 |
| Icons | Lucide React |
| Routing | React Router v6 |
| HTTP | Axios |
| Testing | Vitest + Testing Library |

## Project Structure

```
frontend/src/
├── main.tsx                      # App entry — QueryClient, Router
├── App.tsx                       # Layout + bottom nav + routes
├── types/index.ts                # All TypeScript interfaces (mirrors backend Pydantic models)
├── constants/index.ts            # QUERY_KEYS, pillar display config
├── lib/
│   ├── api.ts                    # All backend API calls — never fetch directly from components
│   └── utils.ts                  # cn(), formatDate(), formatPillar()
├── components/ui/
│   └── Skeleton.tsx              # Loading skeleton atom
└── features/
    ├── todos/
    │   ├── TodayPage.tsx         # Main daily view — tabs: Today, Exercise, Reference, Screenings
    │   ├── PillarSection.tsx     # Groups todos by pillar; routes brief_today to timeline
    │   ├── TodoItem.tsx          # 3-zone row: checkbox | content | detail chevron
    │   ├── TaskDetailDrawer.tsx  # Bottom-sheet: why/how-to/video/safety/related exercises
    │   ├── BriefTodayTimeline.tsx# Time-ordered view for the brief_today pillar
    │   ├── ReferenceTab.tsx      # Read-only cards for nutrition/sleep/cognitive reference items
    │   ├── RotationCard.tsx      # Today's rotation day summary card
    │   ├── RotationWeekView.tsx  # Mon–Sun grid with day-detail panel (v3 + v4 layouts)
    │   └── ScreeningAlert.tsx    # Due/overdue screening alerts
    ├── dashboard/
    │   ├── DashboardPage.tsx     # Benefit score cards + completion tables
    │   ├── BenefitScoreCards.tsx # Animated score chips by health outcome
    │   └── CompletionTable.tsx   # Daily/weekly/monthly completion history
    ├── upload/
    │   └── UploadPage.tsx        # AI Ingest tab + Classic Upload tab
    └── agent/
        └── AgentChat.tsx         # LLM coach chat (uses plan_json context)
```

## Prerequisites

- Node.js 18+
- npm 9+
- Backend running on `http://localhost:8000` (see `../backend/README.md`)

## Setup & Run

```bash
npm install
npm run dev
```

App: **http://localhost:5173**

All `/api/*` requests are proxied to `http://localhost:8000` by Vite — no CORS setup needed in development.

## Available Scripts

| Script | Description |
|---|---|
| `npm run dev` | Start dev server with hot reload |
| `npm run build` | Type-check + production build to `dist/` |
| `npm run preview` | Preview production build locally |
| `npm test` | Run Vitest tests in watch mode |
| `npm run test -- --run` | Run tests once (CI mode) |
| `npx tsc --noEmit` | Type-check without building |
| `npm run lint` | ESLint check |

## Pages & Tabs

| Route | Page | Description |
|---|---|---|
| `/` | Today | Daily task list, exercise rotation, reference, screenings |
| `/dashboard` | Dashboard | Benefit score cards + completion history tables |
| `/upload` | Upload | AI Ingest (recommended) + Classic Upload |
| `/coach` | Coach | AI longevity coach chat |

### Today page tabs

| Tab | What it shows |
|---|---|
| Today | Tasks grouped by pillar; `brief_today` shown as a time-ordered timeline |
| Exercise | Today's rotation day card + Mon–Sun week grid with workout detail |
| Reference | Read-only cards for nutrition, sleep, cognitive, exercise library |
| Screenings | Due and upcoming health screening alerts |

## How to Update Your Plan

No frontend changes needed when you update your spreadsheet.

1. Edit your `.xlsx` workbook — add tasks, rename columns, restructure sheets
2. Open the app → **Upload** tab
3. Choose **AI Ingest** (recommended) — drop your `.xlsx` or `.json`
4. Claude reads every sheet, normalizes the data, saves to DB, pre-generates 30 days of todos
5. All tabs update automatically — TanStack Query refetches on upload success

The frontend never hardcodes pillar names, task names, or schedules. Everything comes from the backend which reads from whatever plan was last ingested.

## Key Components

### TodoItem — 3-zone row
```
[ ✓ checkbox ] [ task name + description + timing ]  [ > chevron ]
  toggles         tappable — shows nothing             opens TaskDetailDrawer
  completion
```

### TaskDetailDrawer
Bottom-sheet that opens when you tap the chevron. Shows:
- Why it matters (why_mechanism)
- How to do it (how_to)
- Safety notes
- Video link button (YouTube demo)
- Reference link (GIF search)
- Related exercises from the exercise library

### RotationWeekView — v3 / v4 aware
The day detail panel automatically detects which workbook version populated the rotation:
- **v4** (time-budget layout): shows warm-up/upper-back/secondary/cool-down minute chips, exercise lists, fits-60-min badge, week rule
- **v3** (block layout): shows warm-up/priority-block/secondary-block/cardio/cool-down/nutrition chips

### BriefTodayTimeline
Tasks from the `brief_today` pillar are sorted by timing (7:00 AM → Evening → Bedtime → Anytime) and displayed in a time-gutter layout instead of a flat list.

## Open Architecture

- Pillar names come from the backend — the frontend renders whatever pillars exist
- Benefit scores and weights come from `benefit_config.json` on the server
- Column names in the spreadsheet don't matter when using AI Ingest
- Adding a new sheet to your workbook automatically creates a new pillar tab

## Phase Roadmap

| Phase | Status | Notes |
|---|---|---|
| 1 — POC | **Current** | Single user, AI ingest, full rotation + screening UI |
| 2 — Multi-user | Planned | OAuth login, user profiles, per-user plans |
| 3 — Reports | Planned | Recharts trend graphs, PDF export, share links |
