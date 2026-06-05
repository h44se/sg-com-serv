# API Contract

This document freezes the backend DTO and endpoint names for the Formula One dashboard.

## Canonical DTOs

- `Meeting`
- `Session`
- `PositionSample`
- `LapSample`
- `RaceControlMessage`
- `ClassificationRow`
- `ChampionshipStandingRow`
- `DashboardSnapshot`

## Internal API endpoints

- `GET /api/dashboard`
- `GET /api/next-race`
- `GET /api/schedule/next`
- `GET /api/countdown`
- `GET /api/results/latest`
- `GET /api/standings/drivers`
- `GET /api/standings/constructors`

## Data rules

- All timestamps are stored as UTC in the backend.
- The frontend is responsible for local timezone display formatting.
- Cache TTLs are endpoint-specific:
  - schedule/next race: hours
  - results/standings: minutes
  - live timing / race control: seconds

## Provider notes

OpenF1 is treated as a provider for meeting/session/live data. Standings and results may require a fallback adapter or a cache-backed derived view if the provider endpoint is unavailable.

- `GET /v1/sessions?session_key=latest` identifies the provider's latest known session, which may already be completed.
- The dashboard's `sessions` list represents open or future sessions for the active meeting, derived from `GET /v1/sessions?meeting_key=...` filtered against the current UTC clock.
- Reusable example capture: `docs/openf1-states/2026-06-05-monaco-mid-weekend.md`
