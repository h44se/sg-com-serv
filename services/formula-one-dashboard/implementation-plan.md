# Formula One Dashboard Implementation Plan

> **For Hermes:** Use the available specialist profiles in parallel where lanes are independent. Start with product/architecture validation, then fan out into backend and frontend implementation, then converge on tests and review.

**Goal:** Build a timezone-aware Formula 1 dashboard that shows the next race, upcoming session schedule, live countdowns, last session results, and current championship tables in one place.

**Architecture:** Use a 3-layer design: a backend aggregation API that normalizes provider data and caches it, a frontend dashboard that renders only internal DTOs, and a small set of shared contracts/types that keep both sides aligned. The backend should hide provider quirks, convert timestamps to UTC internally, and expose stable dashboard endpoints; the frontend should detect the viewer timezone, convert display times locally, and poll for freshness without hammering the provider.

**Tech Stack:** FastAPI, Python 3.12+, Pydantic, httpx, Redis-compatible caching, Next.js App Router, React, TypeScript, Tailwind CSS, TanStack Query, and Zod/typed DTOs for runtime-safe boundaries.

---

## 0. Discovery notes from source validation

The OpenF1 API is reachable in this environment, but the endpoint coverage is not perfectly aligned with the concept doc:

- Working endpoints confirmed:
  - `GET /v1/meetings?meeting_key=latest`
  - `GET /v1/sessions?session_key=latest`
  - `GET /v1/position?session_key=...`
  - `GET /v1/laps?session_key=...`
  - `GET /v1/stints?session_key=...`
  - `GET /v1/pit?session_key=...`
  - `GET /v1/race_control?session_key=...` (can rate-limit)
- Guessed endpoints that returned 404 in this environment:
  - `GET /v1/session_results`
  - `GET /v1/championship_drivers`
  - `GET /v1/championship_teams`
- `weather` and some race-control calls may return 429 under rate limiting.

Implication: build a provider abstraction and treat standings/results as separate adapters or cached derived views instead of hard-coding the concept’s endpoint names.

---

## 1. Assigned profiles and lanes

Use the actual profiles that exist on this machine:

- `product-analyst` — scope validation, source coverage, MVP boundaries
- `architect` — API contract, data model, caching policy, dependency split
- `backend-engineer` — provider adapters, normalization, aggregation API, caching
- `frontend-engineer` — dashboard shell, timezone conversion, polling UI, responsive layout
- `test-engineer` — unit/integration coverage for transforms, cache behavior, and UI states
- `devops-engineer` — env vars, local run instructions, health checks, deployment packaging
- `code-reviewer` — final correctness/maintainability review before merge

Suggested model split already available in the machine config:
- heavier coordination/review work: `architect`, `code-reviewer`
- implementation lanes: `backend-engineer`, `frontend-engineer`, `test-engineer`, `devops-engineer`

---

## 2. Execution graph and parallelization

1. `product-analyst` validates the OpenF1-backed MVP scope and confirms what must fall back to cached/derived data.
2. `architect` freezes the internal contract, endpoint names, and cache TTLs.
3. After the contract is frozen, run two independent lanes in parallel:
   - `backend-engineer` builds provider clients, DTOs, cache wrappers, and internal API handlers.
   - `frontend-engineer` builds the dashboard shell, timezone helpers, and UI components against the agreed DTOs.
4. Once the contract stabilizes, `test-engineer` adds fixtures and tests for transformations, timezone rendering, countdown boundaries, and stale/error states.
5. `devops-engineer` adds local run notes, env documentation, health checks, and deploy packaging.
6. `code-reviewer` does the final pass only after all implementation and tests are complete.

Parallel lanes only start after the contract files exist; do not let the frontend invent its own payload shape.

---

## 3. Work breakdown with bite-sized tasks

### Task 1: Validate MVP scope and provider coverage

**Owner:** `product-analyst`

**Objective:** Confirm the dashboard ships as an OpenF1-centered MVP with explicit fallback behavior for standings/results coverage gaps.

**Files:**
- Create: `/home/flh/.hermes/workspace/formula-one-dashboard/notes/source-validation.md`
- Modify: `/home/flh/.hermes/workspace/formula-one-dashboard/implementation-plan.md`

**Steps:**
1. Write down the confirmed working OpenF1 endpoints and the 404/429 caveats.
2. Mark `session_results` and `championship_*` as provider-risk items requiring fallback or alternate adapters.
3. Define the MVP must-haves vs nice-to-haves.
4. Sign off the exact dashboard sections that are in scope for v1.

**Verification:** The scope doc clearly states what the dashboard can ship with if standings/results are delayed or cached.

---

### Task 2: Freeze backend/frontend contract and cache policy

**Owner:** `architect`

**Objective:** Produce the canonical DTOs and endpoint list that both frontend and backend will use.

**Files:**
- Create: `/home/flh/.hermes/workspace/formula-one-dashboard/docs/api-contract.md`
- Create: `/home/flh/.hermes/workspace/formula-one-dashboard/backend/src/f1dashboard/contracts.py`
- Create: `/home/flh/.hermes/workspace/formula-one-dashboard/frontend/src/lib/dashboard-types.ts`

**Steps:**
1. Define `RaceEvent`, `Session`, `SessionResult`, `ChampionshipStanding`, and `DashboardSnapshot`.
2. Define the API surface: `/api/dashboard`, `/api/next-race`, `/api/schedule/next`, `/api/countdown`, `/api/results/latest`, `/api/standings/drivers`, `/api/standings/constructors`.
3. Freeze cache TTL classes:
   - schedule/next-race: hours
   - results/standings: minutes
   - live timing/race-control/weather: seconds
4. Ensure all timestamps are UTC internally and only converted in the UI.

**Verification:** The DTO file contains stable field names and no frontend-specific formatting logic.

---

### Task 3: Build backend provider adapters and normalized dashboard assembly

**Owner:** `backend-engineer`

**Objective:** Implement a small OpenF1 client, normalized DTO mapping, and a dashboard snapshot service with cache hooks.

**Files:**
- Create: `/home/flh/.hermes/workspace/formula-one-dashboard/backend/src/f1dashboard/providers/openf1.py`
- Create: `/home/flh/.hermes/workspace/formula-one-dashboard/backend/src/f1dashboard/models.py`
- Create: `/home/flh/.hermes/workspace/formula-one-dashboard/backend/src/f1dashboard/services/dashboard.py`
- Create: `/home/flh/.hermes/workspace/formula-one-dashboard/backend/src/f1dashboard/cache.py`

**Steps:**
1. Write a minimal HTTP client wrapper around `https://api.openf1.org`.
2. Implement methods for latest meeting, latest session, position, laps, stints, pit, and race-control.
3. Normalize provider payloads into UTC-based dataclasses.
4. Add a thin cache abstraction with endpoint-specific TTL selection.
5. Assemble a `DashboardSnapshot` from the normalized pieces.

**Verification:** A sample snapshot can be produced from latest meeting/session data without the frontend.

---

### Task 4: Build frontend dashboard shell, timezone utilities, and view models

**Owner:** `frontend-engineer`

**Objective:** Create the dashboard UI scaffold that renders the internal DTOs and handles local timezone conversion.

**Files:**
- Create: `/home/flh/.hermes/workspace/formula-one-dashboard/frontend/src/lib/timezone.ts`
- Create: `/home/flh/.hermes/workspace/formula-one-dashboard/frontend/src/lib/dashboard-client.ts`
- Create: `/home/flh/.hermes/workspace/formula-one-dashboard/frontend/src/components/dashboard/DashboardShell.tsx`
- Create: `/home/flh/.hermes/workspace/formula-one-dashboard/frontend/src/components/dashboard/CountdownTimer.tsx`
- Create: `/home/flh/.hermes/workspace/formula-one-dashboard/frontend/src/components/dashboard/StandingsTable.tsx`

**Steps:**
1. Add timezone detection using the browser IANA timezone name.
2. Implement local display formatting helpers.
3. Add the dashboard shell with loading, empty, and error states.
4. Add countdown rendering that updates client-side every second.
5. Keep the layout mobile-first and responsive.

**Verification:** A static dashboard mock can render with placeholder DTOs and show local times correctly.

---

### Task 5: Add tests for normalization, timezone conversion, and stale-data states

**Owner:** `test-engineer`

**Objective:** Lock in the critical behavior around provider mapping, time conversion, and countdown boundaries.

**Files:**
- Create: `/home/flh/.hermes/workspace/formula-one-dashboard/backend/tests/test_openf1_client.py`
- Create: `/home/flh/.hermes/workspace/formula-one-dashboard/backend/tests/test_dashboard_service.py`
- Create: `/home/flh/.hermes/workspace/formula-one-dashboard/frontend/src/lib/timezone.test.ts`
- Create: `/home/flh/.hermes/workspace/formula-one-dashboard/frontend/src/components/dashboard/__tests__/CountdownTimer.test.tsx`

**Steps:**
1. Add fixture-based tests for OpenF1 normalization.
2. Add boundary tests for countdown transitions.
3. Add timezone-formatting assertions for UTC-to-local conversion.
4. Add stale/error-state assertions for partially missing dashboard payloads.

**Verification:** Tests fail before the implementation exists and pass once the contract is wired.

---

### Task 6: Add devops notes, run instructions, and health checks

**Owner:** `devops-engineer`

**Objective:** Document how to run the stack locally and what to monitor in deployment.

**Files:**
- Create: `/home/flh/.hermes/workspace/formula-one-dashboard/docs/runbook.md`
- Create: `/home/flh/.hermes/workspace/formula-one-dashboard/.env.example`
- Create: `/home/flh/.hermes/workspace/formula-one-dashboard/docker-compose.yml` (optional)

**Steps:**
1. Document required environment variables and cache settings.
2. Add backend health-check and readiness expectations.
3. Document rate-limit handling and stale-cache fallback behavior.
4. Add minimal deploy notes for backend/frontend separation.

**Verification:** A new developer can read the runbook and understand how to start and verify the app.

---

### Task 7: Final review and integration check

**Owner:** `code-reviewer`

**Objective:** Verify the whole implementation for correctness, edge cases, and maintainability.

**Files:**
- Review all files created above.

**Steps:**
1. Confirm backend and frontend use the same DTO names.
2. Check that UTC handling is consistent end-to-end.
3. Verify the fallback story for missing standings/results is explicit.
4. Confirm the caching policy matches the data freshness needs.
5. Approve only when tests and run notes are in place.

**Verification:** Final review produces either APPROVED or a bounded set of fixes.

---

## 4. Delivery order for this session

1. Finish the plan and create the workspace scaffold.
2. Start backend and frontend foundation work in parallel.
3. Add tests immediately after the DTO contract lands.
4. Finish with runbook notes and a review pass.

---

## 5. Definition of done

- The dashboard shows the next race and the next session in the viewer timezone.
- Countdown timers update client-side without re-fetching every second.
- The backend serves normalized UTC DTOs from a provider abstraction.
- Missing standings/results are handled gracefully with an explicit fallback path.
- Tests cover the critical transformation paths.
- The runbook explains how to run and verify the stack.
