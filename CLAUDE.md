# CLAUDE.md

> Standing instructions for Claude Code on this repository.
> Read this file fully before doing any work. These are **rules, not suggestions**.
> If a request conflicts with these rules, follow the rules and say so.

---
## Foundational Principles
@CONSTITUTION.md

## 1. Project Context

| Layer       | Stack                                                                 |
|-------------|-----------------------------------------------------------------------|
| Frontend    | React + TypeScript, Vite, React Router, TanStack Query (data fetching) |
| FE testing  | Vitest + React Testing Library (RTL), `@testing-library/user-event`   |
| Backend     | Python 3.11+, FastAPI, Pydantic v2, Uvicorn (ASGI)                     |
| API docs    | OpenAPI 3.1 auto-generated; Swagger UI at `/docs`, ReDoc at `/redoc`  |
| BE testing  | pytest, `pytest-asyncio`, `httpx.AsyncClient`, `pytest-randomly`      |
| Lint/format | Ruff + mypy (Python); ESLint + Prettier (TypeScript)                  |

Adjust the *specifics* above to match the real repo, but the **workflow in §3 always applies regardless of stack**.

---

## 2. Golden Rules (non-negotiable)

1. **No code is delivered until it has been reviewed at least twice (§4) and covered by tests that have been run at least twice (§5).**
2. **Every test must be proven to fail when the code is wrong.** A test that passes no matter what is worse than no test — it gives false confidence.
3. **Never weaken a test or delete an assertion to make a suite go green.** Fix the code, or fix the test for the *right* reason and explain why.
4. Match existing patterns in the repo before introducing new ones. Consistency beats personal preference.
5. Never commit secrets, API keys, or `.env` contents. Never log credentials, tokens, or PII.
6. If a requirement is ambiguous, state your assumption explicitly in the response — do not guess silently.
7. Prefer the smallest change that fully solves the problem. No unrequested refactors mixed into a feature change.

---

## 3. Mandatory Workflow

Every coding task follows these five phases **in order**. Do not skip ahead.

```
  PLAN  →  IMPLEMENT  →  REVIEW ×2–3  →  WRITE TESTS  →  RUN TESTS ×2
```

### Phase 1 — Plan
- Restate the task in 2–4 sentences: what input, what operation, what output.
- List the files you will touch and why.
- Identify edge cases up front (empty input, nulls, large input, auth failure, network error, concurrent access).
- For non-trivial work, write the plan into the response before writing code.

### Phase 2 — Implement
- Write the implementation following §6 (backend) and §7 (frontend).
- Keep functions small and single-purpose. If a function exceeds ~40 lines or has >3 levels of nesting, split it.
- Type everything: Python type hints + mypy clean; TypeScript with no `any`.

### Phase 3 — Review (TWO passes minimum, THREE for security-sensitive or public-facing code)

Each pass uses a **different lens** — re-reading with the same lens is not a second review.

**Review Pass 1 — Correctness & Spec**
- Does it actually do what the task asked? Compare line by line against the Phase 1 plan.
- Are all edge cases from the plan handled? Empty, null, zero, negative, max-size, malformed.
- Are all error/exception paths handled, not just the happy path?
- Off-by-one, wrong operator, inverted condition, wrong variable used.

**Review Pass 2 — Security & Robustness**
- Input validation: is *every* external input (request body, query param, env var, file) validated before use?
- Injection: SQL/command/path traversal — are inputs parameterized/sanitized?
- AuthN/AuthZ: is the endpoint protected? Does it check the user *owns* the resource, not just that they are logged in?
- Resource safety: connections/files closed, no unbounded loops, no unbounded memory growth.
- Concurrency: shared mutable state, race conditions, async tasks awaited.
- Secrets: nothing hardcoded, nothing logged.

**Review Pass 3 — Maintainability (required for security-sensitive / API-public code; recommended always)**
- Naming: do names describe intent? No `data2`, `tmp`, `helper3`.
- Duplication: is logic repeated that should be extracted?
- Complexity: can a reader understand each function in <30 seconds?
- Docs: docstrings on public functions, comments only where the *why* is non-obvious.
- Dead code, leftover debug prints, commented-out blocks removed.

> In your response, briefly note what each review pass found and fixed. If a pass found nothing, say so explicitly — that is the proof the pass happened.

### Phase 4 — Write Tests
Only after review is clean. See §8 for what to test and how.

### Phase 5 — Run Tests (TWO passes — each pass proves something different)

**Test Pass A — Correctness (the suite is green)**
- Run the full relevant suite. Every test passes.
- Backend: `pytest -q`
- Frontend: `npm run test`

**Test Pass B — Robustness (the suite is *trustworthy*)**
This is the pass most workflows skip. It catches two failure modes:

1. **Flaky / order-dependent tests.** Re-run the suite with randomized order and in isolation. If results change between runs, a test leaks state — fix it.
   - Backend: `pytest -q -p randomly` (run twice; `pytest-randomly` reshuffles each run) and `pytest --lf`.
   - Frontend: `npm run test -- --run` twice; tests must not depend on execution order.

2. **"Fake green" tests.** For each new test, prove it is real: temporarily break the code it covers (flip a condition, return a wrong value) and confirm the test **fails**. Then revert. A test that stays green while the code is broken is testing nothing.

> In your response, confirm both passes ran and that negative-verification was done on the new tests.

---

## 4. Definition of Done

A task is complete only when **all** of the following are true:

- [ ] Code implemented per the Phase 1 plan.
- [ ] Review Pass 1 (correctness) done; findings noted.
- [ ] Review Pass 2 (security) done; findings noted.
- [ ] Review Pass 3 done if security-sensitive/public-facing.
- [ ] Tests written for happy path **and** edge/error cases.
- [ ] Test Pass A: full suite green.
- [ ] Test Pass B: randomized re-run stable + new tests negative-verified.
- [ ] Linters/type-checkers clean: `ruff check`, `mypy`, `eslint`, `tsc --noEmit`.
- [ ] No secrets, no debug prints, no dead code.
- [ ] If an API contract changed, OpenAPI/Swagger reflects it (see §6.4).

---

## 5. Commands Reference

```bash
# --- Backend ---
ruff check . && ruff format --check .   # lint + format check
mypy app                                # type check
pytest -q                               # Test Pass A
pytest -q -p randomly                   # Test Pass B (run twice)
uvicorn app.main:app --reload           # run dev server (Swagger at /docs)

# --- Frontend ---
npm run lint                            # eslint
npx tsc --noEmit                        # type check
npm run test                            # Test Pass A
npm run test -- --run                   # Test Pass B (run twice)
npm run build                           # production build must succeed
```

---

## 6. Backend Rules — FastAPI / Python

### 6.1 Project structure
```
app/
  main.py            # FastAPI() instance, router registration
  api/routes/        # one file per resource (users.py, orders.py)
  schemas/           # Pydantic request/response models
  services/          # business logic — NO FastAPI imports here
  models/            # DB models
  core/              # config, security, dependencies
tests/               # mirrors app/ structure
```
**Routes are thin.** A route function parses the request, calls a service, returns a response. Business logic lives in `services/` so it is testable without HTTP.

### 6.2 Pydantic & validation
- Every request body and response is a Pydantic v2 model. Never accept raw `dict`.
- Use separate models for input vs output (`UserCreate` vs `UserRead`) — never expose password hashes, internal IDs, etc.
- Use `Field(...)` constraints (`min_length`, `ge`, `le`, `pattern`) so invalid input is rejected at the boundary with an automatic 422.

```python
class UserCreate(BaseModel):
    email: EmailStr
    age: int = Field(ge=0, le=120)

class UserRead(BaseModel):
    id: int
    email: EmailStr
    # note: no password field — output model is deliberately narrower
```

### 6.3 Async & errors
- I/O-bound work (DB, HTTP, files) uses `async def`. Do not block the event loop with sync I/O.
- Raise `HTTPException` with a correct status code for expected failures (404 not found, 403 forbidden, 409 conflict, 422 validation).
- Never let an unhandled exception leak a stack trace to the client. Catch, log server-side, return a generic 500 body.

### 6.4 OpenAPI / Swagger
- Give every route a `summary`, a `response_model`, and a `tags` entry — these drive the Swagger UI.
- Document non-200 outcomes with the `responses=` argument so `/docs` shows them.
- After any change to a route signature, request, or response: open `/docs`, confirm the schema is correct, and confirm the example request still works.

```python
@router.post(
    "/users",
    response_model=UserRead,
    status_code=201,
    summary="Create a new user",
    tags=["users"],
    responses={409: {"description": "Email already registered"}},
)
async def create_user(payload: UserCreate) -> UserRead:
    return await user_service.create(payload)
```

### 6.5 Backend testing (pytest)
- Test **services** directly (fast, no HTTP) and **routes** via `httpx.AsyncClient` against the app.
- For every endpoint test at minimum: success (2xx), validation failure (422), not-found (404), and unauthorized (401/403) where applicable.
- Use fixtures for setup; each test must be independent — no test depends on another running first.
- Use a transactional or isolated test DB; never touch a real database.

```python
@pytest.mark.asyncio
async def test_create_user_rejects_bad_email(client: AsyncClient):
    resp = await client.post("/users", json={"email": "not-an-email", "age": 30})
    assert resp.status_code == 422   # validation must reject it
```

---

## 7. Frontend Rules — React / TypeScript

### 7.1 Structure
```
src/
  components/        # reusable, presentational, no data fetching
  features/<name>/   # feature-scoped components + hooks + api
  hooks/             # shared custom hooks
  api/               # typed HTTP client; one module per backend resource
  types/             # shared TS types (mirror backend Pydantic schemas)
```

### 7.2 Components & hooks
- Function components only. Keep components small; extract logic into custom hooks.
- Props are fully typed via an `interface`/`type` — no implicit `any`.
- No business logic or `fetch` calls inside JSX-heavy components. Data fetching goes through the `api/` layer + TanStack Query / a custom hook.
- Manage server state with TanStack Query (handles loading/error/caching); use `useState`/`useReducer` only for local UI state.
- Lists rendered with stable, unique `key` props — never the array index when items can reorder.

### 7.3 API layer & types
- Every backend call goes through a typed function in `api/`. Components never call `fetch` directly.
- TS request/response types must mirror the backend Pydantic models. If the API contract changes, update both sides in the same task.
- Always handle three states in the UI: **loading**, **error**, **success**. Never render assuming data is present.

```typescript
// api/users.ts
export async function createUser(input: UserCreate): Promise<UserRead> {
  const res = await fetch("/api/users", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
  if (!res.ok) throw new Error(`createUser failed: ${res.status}`);
  return (await res.json()) as UserRead;
}
```

### 7.4 Frontend testing (Vitest + RTL)
- Test **behavior the user sees**, not implementation details. Query by role/label/text, not by CSS class or test-id-only.
- Use `@testing-library/user-event` for interactions (clicks, typing) — it simulates real user behavior more faithfully than `fireEvent`.
- Mock the `api/` layer, not `fetch` internals — tests stay valid if the transport changes.
- For every component test cover: renders correctly, the loading state, the error state, and the main user interaction.

```typescript
test("shows validation error for empty email", async () => {
  const user = userEvent.setup();
  render(<SignupForm />);
  await user.click(screen.getByRole("button", { name: /sign up/i }));
  expect(screen.getByText(/email is required/i)).toBeInTheDocument();
});
```

---

## 8. What "Good Test Coverage" Means Here

For any unit of code, tests must cover, at minimum:

1. **Happy path** — correct input produces correct output.
2. **Boundaries** — empty, zero, negative, maximum size, single element.
3. **Invalid input** — wrong type, missing required field, malformed value → expected rejection.
4. **Error paths** — dependency throws, network fails, resource not found.
5. **Auth** (backend) — unauthenticated and unauthorized access are blocked.

Coverage percentage is a signal, not a goal. A 100%-covered function with no edge-case assertions is not tested. Prefer fewer, meaningful tests over many shallow ones.

---

## 9. Communication Rules for Claude

When completing a task, the response must include:
- The Phase 1 plan (for non-trivial work).
- A one-line-per-pass summary of what each review pass found/fixed.
- Confirmation that Test Pass A and Test Pass B both ran, and that new tests were negative-verified.
- Any assumptions made due to ambiguous requirements.

Do not claim a task is done unless every box in §4 (Definition of Done) is checked.
