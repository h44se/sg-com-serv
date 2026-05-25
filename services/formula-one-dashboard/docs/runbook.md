# Runbook

## Local setup

- Backend source: `backend/src/f1dashboard`
- Frontend source: `frontend/src`

## Environment variables

- `OPENF1_BASE_URL` — optional override for the OpenF1 provider base URL
- `DASHBOARD_CACHE_TTL_SECONDS` — optional override for the dashboard cache TTL

## Operational notes

- Treat OpenF1 as a partially rate-limited provider.
- If live data returns 429, fall back to the last cached snapshot instead of failing the page.
- Keep timestamps in UTC until presentation time.
- The frontend should display the browser timezone name so users can verify how the schedule is being converted.

## Health checks

- Backend should expose a simple liveness check when the FastAPI app is added.
- The dashboard should remain usable when live data is stale as long as cached schedule/session data exists.
