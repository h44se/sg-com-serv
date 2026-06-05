# Source Validation Notes

Confirmed in this environment:

- OpenF1 root responds: `https://api.openf1.org/`
- Latest meeting/session endpoints work:
  - `/v1/meetings?meeting_key=latest`
  - `/v1/sessions?session_key=latest`
- Live timing-style endpoints that work:
  - `/v1/position?session_key=...`
  - `/v1/laps?session_key=...`
  - `/v1/stints?session_key=...`
  - `/v1/pit?session_key=...`
  - `/v1/race_control?session_key=...`
- Rate-limiting caveat:
  - `weather` and some `race_control` calls can return HTTP 429
- Not confirmed / not reliable in this environment:
  - `session_results`
  - `championship_drivers`
  - `championship_teams`
- Captured reusable state:
  - Monaco mid-weekend on `2026-06-05`: `latest_session` returned completed `Practice 1` while `sessions?meeting_key=1286` still exposed the remaining open weekend schedule. See `docs/openf1-states/2026-06-05-monaco-mid-weekend.md`.

Conclusion:

- The dashboard should treat OpenF1 as a provider for meetings, sessions, live timing, and race-control data.
- Championship standings and session results need a fallback adapter or a derived/cache-backed path.
- The dashboard must derive the open weekend schedule from meeting sessions plus the current clock, not from `latest_session` alone.
