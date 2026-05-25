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

Conclusion:

- The dashboard should treat OpenF1 as a provider for meetings, sessions, live timing, and race-control data.
- Championship standings and session results need a fallback adapter or a derived/cache-backed path.
