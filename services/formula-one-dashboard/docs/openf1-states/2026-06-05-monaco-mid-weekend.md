# OpenF1 State: Monaco Mid-Weekend

Captured from the live OpenF1 API on `2026-06-05` during the Monaco Grand Prix weekend after `Practice 1` had finished and before `Practice 2` had started.

## Purpose

This state documents an important OpenF1 behavior that the dashboard relies on:

- `latest_meeting` identifies the active weekend.
- `latest_session` identifies the most recently known session.
- the open weekend schedule must be derived from `sessions?meeting_key=...` plus the current clock.

`latest_session` is not the same thing as the next open or upcoming session.

## Capture summary

- Capture date: `2026-06-05`
- Reference clock for app behavior: `2026-06-05T12:45:00Z`
- Meeting: `Monaco Grand Prix` (`meeting_key=1286`)
- Latest session from OpenF1: `Practice 1` (`session_key=11292`)

## Source endpoints

- `GET https://api.openf1.org/v1/meetings?meeting_key=latest`
- `GET https://api.openf1.org/v1/sessions?session_key=latest`
- `GET https://api.openf1.org/v1/sessions?meeting_key=1286`

## Raw provider interpretation

- `meetings?meeting_key=latest` returns the active Monaco weekend.
- `sessions?session_key=latest` returns `Practice 1` because it is the latest completed or active session known at capture time.
- `sessions?meeting_key=1286` returns the full Monaco weekend schedule:
  - `Practice 1` (`11292`)
  - `Practice 2` (`11293`)
  - `Practice 3` (`11294`)
  - `Qualifying` (`11295`)
  - `Race` (`11299`)

## Dashboard interpretation

Using `reference_now_utc = 2026-06-05T12:45:00Z`:

- completed sessions:
  - `Practice 1` (`11292`) because `date_end = 2026-06-05T12:30:00Z`
- open or upcoming sessions:
  - `Practice 2` (`11293`)
  - `Practice 3` (`11294`)
  - `Qualifying` (`11295`)
  - `Race` (`11299`)

The dashboard should not display `Practice 1` in the open weekend schedule for this state even though `latest_session` still points at it.

## Reusable fixture set

Machine-readable fixture files for this capture live in:

- `backend/tests/fixtures/openf1/2026-monaco-mid-weekend/`

Files:

- `meetings-latest.json`
- `sessions-latest.json`
- `sessions-meeting-1286.json`
- `manifest.json`

The fixture set is intended for regression tests and future provider-behavior documentation.
