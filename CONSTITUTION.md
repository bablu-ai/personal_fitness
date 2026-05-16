# Project Constitution: [App Name]
> **Version:** 2.0 | **Last Updated:** 2026-05-15
> **Guiding Principle:** Ship a working POC first, then harden. Security is layered in — not bolted on at the end.

---

## 📌 Development Philosophy: Two-Phase Approach

> Claude must always be aware of the current phase. Confirm the phase at the start of every session.

### Phase 1 — Proof of Concept (POC)
- **Goal:** Make it work. Validate the idea, the flows, and the UX.
- Stub authentication (mock user, hardcoded tokens are acceptable).
- No production secrets, no real credentials.
- Skip rate limiting, audit logging, and OWASP hardening for now.
- Clearly mark all insecure shortcuts with: `// TODO[SECURITY]: <reason>`
- All API calls should be wrapped in try/catch even in POC.

### Phase 2 — Security & Production Hardening
- Activate all sections in this Constitution marked `[PHASE 2]`.
- Resolve every `// TODO[SECURITY]` comment.
- Run OWASP checklist before any public or client-facing deployment.
- Run OWASP LLM checklist if any AI/LLM feature is in scope.
- Enable structured logging, alerting, and error monitoring.

---

## 1. Tech Stack & Environment

| Layer | Technology |
|---|---|
| Framework | React / Vite (Web) or Expo (Mobile) |
| State — Server | TanStack Query |
| State — Client | Zustand |
| Styling | Tailwind CSS / NativeWind |
| Icons | Lucide React / Lucide React Native |
| Components | Radix UI / Shadcn |
| Auth | NextAuth / Supabase Auth / Clerk (choose one per project) |
| LLM Integration | Vercel AI SDK / LangChain.js / direct provider SDK |
| Logging | Pino (structured) + Sentry (errors) |
| Testing | Vitest + Testing Library + Playwright (e2e) |

---

## 2. Coding Standards (The "Vibe")

### General
- **Functional Components:** Use arrow functions (`const App = () => ...`).
- **TypeScript:** Strict mode enabled. No `any`. Use `interface` for props, `type` for unions/aliases.
- **No magic numbers:** All constants in `/src/constants/` using `UPPER_SNAKE_CASE`.

### File Structure
```
/src
  /components/ui        # Atomic, reusable elements
  /hooks                # Custom hooks (useAuth, useLLM, etc.)
  /features             # Domain-specific logic (feature slices)
  /lib                  # Utility functions, API clients
  /constants            # App-wide constants
  /types                # Shared TypeScript types/interfaces
  /security             # [PHASE 2] Auth guards, validators, sanitizers
  /logging              # [PHASE 2] Logger config, audit trail helpers
```

### Naming
- Components: `PascalCase` → `PrimaryButton.tsx`
- Hooks: `camelCase` with `use` prefix → `useAuth.ts`
- Constants: `UPPER_SNAKE_CASE` → `MAX_RETRY_COUNT`
- Security utilities: `camelCase` with descriptive intent → `sanitizeUserInput.ts`

---

## 3. UI/UX Principles

- **Mobile First:** All layouts must be responsive. Touch targets minimum **44×44px**.
- **Design System:** Use the Tailwind config for all spacing and colors. No inline magic numbers.
- **Loading States:** Always provide a `Skeleton` or `Loader` component for async operations.
- **Accessibility:** Use semantic HTML (`<button>`, `<nav>`, `<main>`). Add `aria-label` and `role` where needed.
- **Error UX:** User-facing errors must be human-readable. Never expose stack traces or system errors in the UI.

---

## 4. Claude-Specific Instructions

- **Refactoring:** When asked to "clean up," prioritize readability over clever one-liners.
- **Error Handling:** Always wrap API calls in `try/catch`. Always provide user-facing error messages.
- **Comments:** Only comment on *"the why,"* not *"the what."* No obvious comments.
- **Testing:** Auto-generate Vitest + Testing Library tests for every new feature.
- **Security TODOs:** When skipping a security control in Phase 1, always add `// TODO[SECURITY]: <reason>`.
- **No secrets in code:** Never hardcode API keys, tokens, or credentials — even in POC. Use `.env` and `.env.example`.

---

## 5. Authentication & Login Security [PHASE 2]

> In Phase 1, stub auth is acceptable. In Phase 2, enforce all of the following.

### Authentication Rules
- Use a proven auth provider (NextAuth, Supabase Auth, Clerk) — **never roll your own auth**.
- Passwords must be hashed with **bcrypt** (min cost factor 12) or **Argon2id** — never MD5/SHA1.
- Enforce **Multi-Factor Authentication (MFA)** for admin and privileged roles.
- Session tokens must be **short-lived** (15–60 min) with silent refresh via **httpOnly** refresh tokens.
- Implement **account lockout** after 5–10 failed login attempts with exponential backoff.
- All authentication events (login, logout, failed attempt, MFA challenge) must be **audit logged**.
- Support **passwordless / passkey (WebAuthn)** options where UX allows.

### Session & Token Management
- Store access tokens in memory only (never `localStorage` — XSS risk).
- Store refresh tokens in **httpOnly, Secure, SameSite=Strict** cookies.
- Rotate refresh tokens on every use (refresh token rotation).
- Invalidate all sessions on password change or account compromise detection.
- JWT claims must include: `iss`, `sub`, `aud`, `exp`, `iat`, `jti` (for revocation).

### Authorization
- Enforce **Role-Based Access Control (RBAC)** or **Attribute-Based Access Control (ABAC)**.
- Validate permissions **server-side** on every request — never trust client-side role checks alone.
- Apply **principle of least privilege** — default deny, explicit allow.

---

## 6. OWASP Top 10 — Web Application Security [PHASE 2]

> Reference: OWASP Top 10 2021 — https://owasp.org/www-project-top-ten/
> Claude must address each item before any production deployment.

### A01 — Broken Access Control
- [ ] Implement server-side authorization checks on every API route.
- [ ] Deny access by default; explicitly grant permissions.
- [ ] Never expose object IDs directly — use opaque references or UUIDs.
- [ ] Log all access control failures and alert on repeated violations.

### A02 — Cryptographic Failures
- [ ] Enforce HTTPS everywhere (HSTS with preload, min 1 year).
- [ ] No sensitive data (passwords, PII, tokens) in logs, URLs, or error messages.
- [ ] Use AES-256-GCM for data at rest encryption where needed.
- [ ] Rotate all secrets and keys on a defined schedule.

### A03 — Injection (SQLi, NoSQLi, Command, LDAP)
- [ ] Use parameterized queries / prepared statements — **never string-concatenate SQL**.
- [ ] Use an ORM (Prisma, Drizzle) with type-safe queries.
- [ ] Validate and sanitize **all** user input server-side (Zod, Yup, or Joi schemas).
- [ ] Reject unexpected fields (strict schema validation — no passthrough).

### A04 — Insecure Design
- [ ] Threat model new features before building.
- [ ] Design rate limiting and abuse prevention into the architecture, not as an afterthought.
- [ ] Apply defense-in-depth — multiple independent security controls.

### A05 — Security Misconfiguration
- [ ] Disable verbose error messages in production (generic errors to users, full details to logs only).
- [ ] Remove all debug endpoints, test accounts, and default credentials before shipping.
- [ ] Set security headers: Content-Security-Policy, X-Frame-Options, X-Content-Type-Options, Referrer-Policy, Permissions-Policy.
- [ ] Use Helmet.js or equivalent middleware.
- [ ] Disable unused HTTP methods on API routes.

### A06 — Vulnerable & Outdated Components
- [ ] Run `npm audit` in CI/CD on every build — fail on high/critical.
- [ ] Use Dependabot or Renovate for automated dependency updates.
- [ ] Pin dependency versions in production (package-lock.json committed).
- [ ] Maintain a Software Bill of Materials (SBOM) for audits.

### A07 — Identification & Authentication Failures
- [ ] See Section 5 (Authentication & Login Security) above.
- [ ] Implement credential stuffing protection (rate limiting + CAPTCHA on login).
- [ ] Never expose whether a username/email exists during login failures (generic error messages).

### A08 — Software & Data Integrity Failures
- [ ] Verify integrity of third-party scripts (Subresource Integrity — SRI hashes).
- [ ] Use signed commits and protect main branch in Git.
- [ ] CI/CD pipeline must include security scanning (e.g., Snyk, OWASP Dependency-Check).
- [ ] Validate deserialized data schemas strictly.

### A09 — Security Logging & Monitoring Failures
- [ ] See Section 8 (Logging & Observability) below.
- [ ] Alert on: repeated auth failures, privilege escalations, mass data access, anomalous API usage.
- [ ] Logs must be tamper-evident and shipped to a separate log aggregation service.

### A10 — Server-Side Request Forgery (SSRF)
- [ ] Validate and allowlist all URLs before making server-side HTTP requests.
- [ ] Block requests to internal IP ranges (169.254.x.x, 10.x.x.x, 172.16.x.x, 192.168.x.x).
- [ ] Never follow redirects blindly in server-side fetch calls.
- [ ] Use a dedicated HTTP client with strict timeout and redirect policies.

---

## 7. OWASP LLM Top 10 — AI / LLM Feature Security [PHASE 2]

> Reference: OWASP Top 10 for LLM Applications 2025 — https://owasp.org/www-project-top-10-for-large-language-model-applications/
> Apply these controls to **any feature using an LLM, AI agent, or deep agent**.

### LLM01 — Prompt Injection
- [ ] **Never trust user-supplied content as instructions.** Clearly separate system prompts from user data.
- [ ] Use structured input/output formats (JSON schemas) to constrain LLM responses.
- [ ] Validate and sanitize all user inputs before interpolating into prompts.
- [ ] Apply a prompt firewall / input guard (e.g., Rebuff, LLM Guard, or custom classifier).
- [ ] For agents: never allow raw user input to control tool selection or execution paths.
- [ ] Treat indirect injection (from retrieved documents, URLs, emails) with the same scrutiny as direct injection.

### LLM02 — Sensitive Information Disclosure
- [ ] Never include PII, secrets, or internal system details in prompts sent to external LLM APIs.
- [ ] Apply output filtering to detect and redact PII before displaying LLM responses.
- [ ] Use data minimization — send only what the LLM strictly needs to complete the task.
- [ ] Log what data is sent to LLM providers (subject to your privacy policy and user consent).

### LLM03 — Supply Chain Vulnerabilities
- [ ] Pin versions of all AI SDKs (LangChain, Vercel AI SDK, OpenAI SDK) — use lock files.
- [ ] Audit third-party plugins, tools, and model providers before integration.
- [ ] Review fine-tuned models or embeddings for poisoned training data risks.
- [ ] Verify integrity of downloaded model weights or adapters (checksums/signatures).

### LLM04 — Data and Model Poisoning
- [ ] Validate and curate training data, RAG document sources, and fine-tuning datasets.
- [ ] Monitor for anomalous model behavior that may indicate poisoning.
- [ ] Restrict who can update RAG knowledge bases or vector stores (admin-only, audited).
- [ ] Implement rollback capability for model/data updates.

### LLM05 — Improper Output Handling
- [ ] Never render raw LLM output as HTML without sanitization (XSS risk).
- [ ] Parse and validate structured outputs against a schema (Zod) before use.
- [ ] Escape all LLM-generated content before inserting into SQL, shell commands, or system calls.
- [ ] Treat LLM output as untrusted user input for downstream processing.

### LLM06 — Excessive Agency (Agentic AI)
- [ ] Apply **principle of least privilege** to all agent tool permissions.
- [ ] Require **human-in-the-loop confirmation** for irreversible actions (delete, send, purchase).
- [ ] Implement **scope boundaries** — agents must not acquire permissions beyond what is defined.
- [ ] Log every tool call an agent makes with full context (what, why, when, who triggered it).
- [ ] Implement a kill switch / pause mechanism for all autonomous agent flows.

### LLM07 — System Prompt Leakage
- [ ] Treat system prompts as confidential — do not expose them in client-side code.
- [ ] Proxy all LLM API calls through a backend — **never call LLM APIs directly from the client**.
- [ ] Test for prompt extraction attacks before deploying AI features.
- [ ] Do not store system prompts in version control if they contain business-sensitive logic.

### LLM08 — Vector and Embedding Weaknesses
- [ ] Validate and sanitize documents before embedding them into vector stores.
- [ ] Apply access control to vector store queries — users must not retrieve other users' embedded data.
- [ ] Monitor for embedding inversion attacks on sensitive data.
- [ ] Avoid embedding highly sensitive PII into shared vector databases.

### LLM09 — Misinformation
- [ ] Do not present LLM output as authoritative fact without grounding/verification.
- [ ] Implement Retrieval Augmented Generation (RAG) with cited, verifiable sources.
- [ ] Add user-visible disclaimers for AI-generated content.
- [ ] Build human review workflows for high-stakes LLM outputs (medical, legal, financial).

### LLM10 — Unbounded Consumption (DoS / Resource Exhaustion)
- [ ] Enforce per-user and per-session **token limits** and **rate limits** on LLM API calls.
- [ ] Set **maximum prompt length** and **maximum response length** limits server-side.
- [ ] Implement cost monitoring and alerting (e.g., alert when daily LLM spend exceeds threshold).
- [ ] Queue long-running LLM tasks — do not block HTTP requests waiting for LLM responses.
- [ ] Implement request timeouts and circuit breakers on all LLM API calls.

---

## 8. Logging & Observability [PHASE 2]

> In Phase 1, console.log is acceptable. In Phase 2, replace with structured logging.

### Logging Standards
- Use **Pino** (Node/server) for structured JSON logging. No console.log in production.
- Every log entry must include: timestamp, level, service, traceId, userId (if authenticated).
- Log levels: fatal | error | warn | info | debug | trace
- Ship logs to a centralized service (Datadog, Logtail, Axiom, or self-hosted ELK).

### What to Log

| Event | Level | Notes |
|---|---|---|
| App startup / shutdown | info | Include version and environment |
| Incoming API requests | info | Method, path, status, latency — no request body |
| Auth success | info | userId, IP, method |
| Auth failure | warn | Attempt count, IP — no password |
| Authorization denial | warn | userId, resource, action attempted |
| Validation errors | warn | Field names only — no values |
| LLM API calls | info | Model, token count, latency — no prompt content if sensitive |
| LLM agent tool calls | info | Tool name, input summary, output summary |
| Unhandled exceptions | error | Full stack trace to logs, generic message to user |
| Security anomalies | error | Rate limit hit, SSRF attempt, injection pattern detected |
| Data mutations (CRUD) | info | Who, what, when — for audit trail |

### What Never to Log
- Passwords, tokens, API keys, or secrets (in any field).
- Full credit card numbers, SSNs, or sensitive PII.
- Full request/response bodies unless explicitly needed and encrypted at rest.
- System prompt content if it contains proprietary business logic.

### Error Monitoring
- Integrate **Sentry** (or equivalent) for real-time error tracking and alerting.
- Set up alerts for: error rate spikes, p99 latency degradation, LLM cost anomalies.
- Every unhandled error must create a Sentry issue with traceId for cross-referencing with logs.

---

## 9. Deployment & CI/CD Security

### Git & Branching
- `main` is **protected**. No direct pushes. PRs require at least one review.
- Feature branches: `feat/feature-name`
- Security fixes: `fix/security-description` (fast-tracked review)
- Commits follow **Conventional Commits**: feat:, fix:, chore:, security:, docs:

### CI/CD Pipeline (Phase 2 gates)
```
[Push] -> [Lint + TypeCheck] -> [Unit Tests] -> [npm audit] -> [SAST Scan] -> [Build] -> [Deploy]
```
- **Fail** the build on any high/critical npm audit finding.
- **Fail** the build on TypeScript errors — strict mode enforced.
- Run SAST (e.g., Semgrep, CodeQL) on every PR.
- Secrets scanning (e.g., Gitleaks, TruffleHog) on every commit.
- Container scans (Trivy) if using Docker.

### Environment & Secrets
- Use `.env.example` with placeholder values — commit this.
- Never commit `.env` or any file containing real secrets.
- Rotate secrets on any suspected exposure — treat as compromised immediately.
- Use a secrets manager (Doppler, AWS Secrets Manager, Vault) in production.

---

## 10. How to Use This Constitution with Claude Code

### Starting a Session
```
Read CONSTITUTION.md and use it as the source of truth for all code generation
and architectural decisions. Ask me which phase (1 or 2) we are in before starting.
```

### Keeping It Updated
If Claude makes a mistake twice (e.g., using useState when you want Zustand, or forgetting to sanitize an LLM output), add a bullet point to the relevant section. Claude will adapt immediately.

### Phase Transition Checklist
Before moving from Phase 1 -> Phase 2, confirm:
- [ ] All // TODO[SECURITY] comments are resolved.
- [ ] OWASP Top 10 checklist reviewed and addressed.
- [ ] OWASP LLM Top 10 checklist reviewed if AI features are present.
- [ ] Structured logging enabled and tested.
- [ ] Auth hardening complete (real tokens, MFA, session management).
- [ ] CI/CD security gates enabled.
- [ ] Secrets moved to a secrets manager.
- [ ] Penetration test or security review scheduled.

---

*This Constitution is a living document. Update it as the project evolves.*
