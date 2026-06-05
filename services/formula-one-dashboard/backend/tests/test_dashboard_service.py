from __future__ import annotations

from datetime import datetime, timezone
from json import loads
from pathlib import Path

import pytest

from f1dashboard.cache import MemoryTTLCache
from f1dashboard.models import DashboardSnapshot
from f1dashboard.providers.jolpica import JolpicaClient
from f1dashboard.providers.jolpica import JolpicaError
from f1dashboard.providers.openf1 import OpenF1Error
from f1dashboard.providers.venue import VenueError
from f1dashboard.services.dashboard import DashboardService


FIXTURES_DIR = Path(__file__).parent / "fixtures" / "openf1"


class FakeClient:
    def latest_meeting(self):
        return {
            "meeting_key": 1285,
            "meeting_name": "Canadian Grand Prix",
            "meeting_official_name": "FORMULA 1 GRAND PRIX DU CANADA 2026",
            "location": "Montréal",
            "country_code": "CAN",
            "country_name": "Canada",
            "circuit_short_name": "Montreal",
            "circuit_image": "https://media.formula1.com/content/dam/fom-website/2018-redesign-assets/Track%20icons%204x3/Canada%20carbon.png",
            "circuit_info_url": "https://api.multiviewer.app/api/v1/circuits/23/2026",
            "date_start": "2026-05-22T16:30:00+00:00",
            "date_end": "2026-05-24T22:00:00+00:00",
        }

    def latest_session(self):
        return {
            "session_key": 11282,
            "meeting_key": 1285,
            "session_name": "Sprint Qualifying",
            "session_type": "Qualifying",
            "date_start": "2026-05-22T20:30:00+00:00",
            "date_end": "2026-05-22T21:14:00+00:00",
        }

    def meetings(self, year):
        return [
            self.latest_meeting(),
            {
                "meeting_key": 1286,
                "meeting_name": "Monaco Grand Prix",
                "meeting_official_name": "FORMULA 1 GRAND PRIX DE MONACO 2026",
                "location": "Monte Carlo",
                "country_code": "MON",
                "country_name": "Monaco",
                "circuit_short_name": "Monaco",
                "circuit_image": "https://media.formula1.com/monaco.png",
                "circuit_info_url": "https://api.multiviewer.app/api/v1/circuits/22/2026",
                "date_start": "2026-06-05T11:30:00+00:00",
                "date_end": "2026-06-07T15:00:00+00:00",
                "is_cancelled": False,
            },
        ] if year == 2026 else []

    def sessions(self, meeting_key):
        if meeting_key == 1286:
            return [
                {
                    "session_key": 11292,
                    "meeting_key": meeting_key,
                    "session_name": "Practice 1",
                    "session_type": "Practice",
                    "date_start": "2026-06-05T11:30:00+00:00",
                    "date_end": "2026-06-05T12:30:00+00:00",
                },
                {
                    "session_key": 11296,
                    "meeting_key": meeting_key,
                    "session_name": "Race",
                    "session_type": "Race",
                    "date_start": "2026-06-07T13:00:00+00:00",
                    "date_end": "2026-06-07T15:00:00+00:00",
                },
            ]
        return [
            self.latest_session(),
            {
                "session_key": 11283,
                "meeting_key": meeting_key,
                "session_name": "Sprint",
                "session_type": "Race",
                "date_start": "2026-05-23T18:00:00+00:00",
                "date_end": "2026-05-23T19:00:00+00:00",
            },
            {
                "session_key": 11284,
                "meeting_key": meeting_key,
                "session_name": "Grand Prix",
                "session_type": "Race",
                "date_start": "2026-05-24T20:00:00+00:00",
                "date_end": "2026-05-24T22:00:00+00:00",
            },
        ]

    def future_sessions(self, since_utc_iso):
        rows = []
        for meeting in self.meetings(2026):
            rows.extend(self.sessions(meeting["meeting_key"]))
        return rows

    def positions(self, session_key):
        return [
            {
                "date": "2026-05-22T20:32:48.586000+00:00",
                "session_key": session_key,
                "meeting_key": 1285,
                "driver_number": 12,
                "position": 2,
            },
            {
                "date": "2026-05-22T20:32:48.586000+00:00",
                "session_key": session_key,
                "meeting_key": 1285,
                "driver_number": 44,
                "position": 1,
            },
            {
                "date": "2026-05-22T21:33:47.284000+00:00",
                "session_key": session_key,
                "meeting_key": 1285,
                "driver_number": 12,
                "position": 1,
            },
            {
                "date": "2026-05-22T21:33:47.284000+00:00",
                "session_key": session_key,
                "meeting_key": 1285,
                "driver_number": 44,
                "position": 2,
            },
        ]

    def drivers(self, session_key):
        return [
            {
                "session_key": session_key,
                "driver_number": 12,
                "full_name": "Andrea Kimi ANTONELLI",
                "team_name": "Mercedes",
            },
            {
                "session_key": session_key,
                "driver_number": 44,
                "full_name": "Lewis HAMILTON",
                "team_name": "Ferrari",
            },
        ]


class FixtureMidWeekendMonacoClient:
    fixture_dir = FIXTURES_DIR / "2026-monaco-mid-weekend"

    def _load(self, name: str):
        return loads((self.fixture_dir / name).read_text(encoding="utf-8"))

    def latest_meeting(self):
        return self._load("meetings-latest.json")[0]

    def latest_session(self):
        return self._load("sessions-latest.json")[0]

    def meetings(self, year):
        if year != 2026:
            return []
        return [self.latest_meeting()]

    def sessions(self, meeting_key):
        if meeting_key != 1286:
            return []
        return self._load("sessions-meeting-1286.json")

    def future_sessions(self, since_utc_iso):
        return self._load("sessions-meeting-1286.json")

    def positions(self, session_key):
        return []

    def drivers(self, session_key):
        return []

    def laps(self, session_key):
        return []

    def stints(self, session_key):
        return []

    def pit(self, session_key):
        return []

    def race_control(self, session_key):
        return []

    def laps(self, session_key):
        return [
            {
                "meeting_key": 1285,
                "session_key": session_key,
                "driver_number": 44,
                "lap_number": 1,
                "date_start": None,
                "lap_duration": 73.25,
            },
            {
                "meeting_key": 1285,
                "session_key": session_key,
                "driver_number": 12,
                "lap_number": 16,
                "date_start": "2026-05-22T21:33:47.284000+00:00",
                "lap_duration": 72.965,
            },
        ]

    def pit(self, session_key):
        return [
            {"meeting_key": 1285, "session_key": session_key, "driver_number": 12, "pit_duration": 349.9},
            {"meeting_key": 1285, "session_key": session_key, "driver_number": 44, "pit_duration": 349.9},
            {"meeting_key": 1285, "session_key": session_key, "driver_number": 63, "pit_duration": 349.9},
        ]

    def race_control(self, session_key):
        return [
            {
                "meeting_key": 1285,
                "session_key": session_key,
                "date": "2026-05-22T20:30:00.066000+00:00",
                "category": "SessionStatus",
                "message": "SESSION STARTED",
            }
        ]


class FakeStandingsClient:
    def driver_standings(self):
        return [
            {
                "position": "1",
                "points": "100",
                "wins": "3",
                "Driver": {
                    "driverId": "antonelli",
                    "givenName": "Kimi",
                    "familyName": "Antonelli",
                },
            }
        ]

    def constructor_standings(self):
        return [
            {
                "position": "1",
                "points": "180",
                "wins": "4",
                "Constructor": {
                    "constructorId": "mercedes",
                    "name": "Mercedes",
                },
            }
        ]
    def latest_race_results(self):
        return {
            "round": "7",
            "raceName": "Monaco Grand Prix",
            "date": "2026-05-24",
            "time": "13:00:00Z",
            "Results": [
                {
                    "position": "1",
                    "number": "12",
                    "points": "25",
                    "Driver": {"givenName": "Kimi", "familyName": "Antonelli", "permanentNumber": "12"},
                    "Constructor": {"name": "Mercedes"},
                },
                {
                    "position": "2",
                    "number": "44",
                    "points": "18",
                    "Driver": {"givenName": "Lewis", "familyName": "Hamilton", "permanentNumber": "44"},
                    "Constructor": {"name": "Ferrari"},
                },
            ],
        }

    def latest_qualifying_results(self):
        return {
            "round": "7",
            "raceName": "Monaco Grand Prix",
            "date": "2026-05-23",
            "time": "14:00:00Z",
            "QualifyingResults": [],
        }


class FakeVenueClient:
    def resolve_circuit(self, meeting_raw):
        return {
            "circuit_name": "Circuit Gilles Villeneuve",
            "circuit_short_name": meeting_raw.get("circuit_short_name"),
            "circuit_image_url": meeting_raw.get("circuit_image"),
            "circuit_wiki_url": "https://en.wikipedia.org/wiki/Circuit_Gilles_Villeneuve",
            "track_map_svg": "<svg viewBox='0 0 10 10'><path d='M1 1 L9 9'/></svg>",
            "track_length_km": 4.361,
            "latitude": 45.5007,
            "longitude": -73.5228,
        }

    def weather_forecast(self, latitude, longitude, start_date, end_date):
        return [
            {
                "date": "2026-05-22",
                "label": "Fri",
                "summary": "Dry",
                "is_wet": False,
                "precipitation_probability_max": 10,
                "precipitation_sum_mm": 0.0,
                "rain_sum_mm": 0.0,
                "showers_sum_mm": 0.0,
                "snowfall_sum_mm": 0.0,
                "temperature_max_c": 20.0,
                "temperature_min_c": 12.0,
            },
            {
                "date": "2026-05-23",
                "label": "Sat",
                "summary": "Wet",
                "is_wet": True,
                "precipitation_probability_max": 70,
                "precipitation_sum_mm": 5.2,
                "rain_sum_mm": 5.2,
                "showers_sum_mm": 0.0,
                "snowfall_sum_mm": 0.0,
                "temperature_max_c": 18.0,
                "temperature_min_c": 11.0,
            },
            {
                "date": "2026-05-24",
                "label": "Sun",
                "summary": "Dry",
                "is_wet": False,
                "precipitation_probability_max": 20,
                "precipitation_sum_mm": 0.1,
                "rain_sum_mm": 0.1,
                "showers_sum_mm": 0.0,
                "snowfall_sum_mm": 0.0,
                "temperature_max_c": 22.0,
                "temperature_min_c": 13.0,
            },
        ]


class BrokenStandingsClient(FakeStandingsClient):
    def driver_standings(self):
        raise JolpicaError("Jolpica request failed")

    def constructor_standings(self):
        raise JolpicaError("Jolpica request failed")


class TimeoutStandingsClient(FakeStandingsClient):
    def latest_race_results(self):
        raise JolpicaError("Jolpica request timed out")

    def latest_qualifying_results(self):
        raise JolpicaError("Jolpica request timed out")


class BrokenVenueClient(FakeVenueClient):
    def resolve_circuit(self, meeting_raw):
        raise VenueError("Venue request timed out")


def test_dashboard_service_builds_a_snapshot() -> None:
    service = DashboardService(
        client=FakeClient(),
        standings_client=FakeStandingsClient(),
        venue_client=FakeVenueClient(),
        clock=lambda: datetime(2026, 5, 23, 14, 0, tzinfo=timezone.utc),
    )
    snapshot = service.get_snapshot(refresh=True)

    assert isinstance(snapshot, DashboardSnapshot)
    assert snapshot.meeting is not None
    assert snapshot.meeting.meeting_name == "Canadian Grand Prix"
    assert snapshot.sessions[0].session_name == "Sprint"
    assert snapshot.sessions[0].date_start_utc > datetime(2026, 5, 23, 14, 0, tzinfo=timezone.utc)
    assert [session.session_name for session in snapshot.sessions] == ["Sprint", "Grand Prix"]
    assert snapshot.latest_positions == []
    assert snapshot.latest_results[0].position == 1
    assert snapshot.latest_results[0].driver_number == 12
    assert snapshot.latest_results[0].driver_name == "Kimi Antonelli"
    assert snapshot.latest_results[0].team_name == "Mercedes"
    assert snapshot.latest_results[0].points == 25
    assert snapshot.latest_results[0].status == "Race result"
    assert snapshot.latest_results[1].position == 2
    assert snapshot.latest_results[1].driver_number == 44
    assert snapshot.race_control == []
    assert snapshot.driver_standings[0].competitor_name == "Kimi Antonelli"
    assert snapshot.driver_standings[0].points == 100
    assert snapshot.constructor_standings[0].competitor_name == "Mercedes"
    assert snapshot.constructor_standings[0].wins == 4
    assert snapshot.venue is not None
    assert snapshot.venue.circuit_name == "Circuit Gilles Villeneuve"
    assert snapshot.venue.track_length_km == 4.361
    assert snapshot.venue.fastest_lap_seconds is None
    assert snapshot.venue.average_pit_stop_seconds == 3.499
    assert len(snapshot.venue.weather_forecast) == 3
    assert snapshot.venue.weather_forecast[1].is_wet is True
    assert snapshot.generated_at_utc.tzinfo == timezone.utc


def test_dashboard_service_keeps_ongoing_session_in_open_schedule() -> None:
    service = DashboardService(
        client=FakeClient(),
        standings_client=FakeStandingsClient(),
        venue_client=FakeVenueClient(),
        clock=lambda: datetime(2026, 5, 22, 20, 45, tzinfo=timezone.utc),
    )

    snapshot = service.get_snapshot(refresh=True)

    assert snapshot.meeting is not None
    assert [session.session_name for session in snapshot.sessions] == ["Sprint Qualifying", "Sprint", "Grand Prix"]
    assert snapshot.sessions[0].date_start_utc < datetime(2026, 5, 22, 20, 45, tzinfo=timezone.utc)
    assert snapshot.sessions[0].date_end_utc > datetime(2026, 5, 22, 20, 45, tzinfo=timezone.utc)


def test_dashboard_service_skips_completed_latest_meeting_for_next_session() -> None:
    service = DashboardService(
        client=FakeClient(),
        standings_client=FakeStandingsClient(),
        venue_client=FakeVenueClient(),
        clock=lambda: datetime(2026, 5, 25, 7, 30, tzinfo=timezone.utc),
    )

    snapshot = service.get_snapshot(refresh=True)

    assert snapshot.meeting is not None
    assert snapshot.meeting.meeting_name == "Monaco Grand Prix"
    assert snapshot.meeting.country_name == "Monaco"
    assert [session.session_name for session in snapshot.sessions] == ["Practice 1", "Race"]
    assert snapshot.sessions[0].date_start_utc == datetime(2026, 6, 5, 11, 30, tzinfo=timezone.utc)


def test_dashboard_service_uses_fixture_mid_weekend_state_to_drop_completed_session() -> None:
    service = DashboardService(
        client=FixtureMidWeekendMonacoClient(),
        standings_client=FakeStandingsClient(),
        venue_client=FakeVenueClient(),
        clock=lambda: datetime(2026, 6, 5, 12, 45, tzinfo=timezone.utc),
    )

    snapshot = service.get_snapshot(refresh=True)

    assert snapshot.meeting is not None
    assert snapshot.meeting.meeting_name == "Monaco Grand Prix"
    assert [session.session_name for session in snapshot.sessions] == ["Practice 2", "Practice 3", "Qualifying", "Race"]
    assert [session.session_key for session in snapshot.sessions] == [11293, 11294, 11295, 11299]


class MeetingSessionsRateLimitedClient(FakeClient):
    def sessions(self, meeting_key):
        raise OpenF1Error("OpenF1 request failed: 429 Too Many Requests")

    def future_sessions(self, since_utc_iso):
        rows = []
        for meeting in FakeClient.meetings(self, 2026):
            rows.extend(FakeClient.sessions(self, meeting["meeting_key"]))
        return rows


def test_dashboard_service_falls_back_to_future_sessions_when_meeting_sessions_fail() -> None:
    service = DashboardService(
        client=MeetingSessionsRateLimitedClient(),
        standings_client=FakeStandingsClient(),
        venue_client=FakeVenueClient(),
        clock=lambda: datetime(2026, 5, 25, 7, 30, tzinfo=timezone.utc),
    )

    snapshot = service.get_snapshot(refresh=True)

    assert snapshot.meeting is not None
    assert snapshot.meeting.meeting_name == "Monaco Grand Prix"
    assert snapshot.sessions[0].session_name == "Practice 1"


class RateLimitedClient(FakeClient):
    def latest_meeting(self):
        raise OpenF1Error("OpenF1 request failed: 429 Too Many Requests")

    def latest_session(self):
        raise OpenF1Error("OpenF1 request failed: 429 Too Many Requests")


class AuthLockedClient(FakeClient):
    def latest_meeting(self):
        raise OpenF1Error("OpenF1 request failed: 401 Unauthorized")

    def latest_session(self):
        raise OpenF1Error("OpenF1 request failed: 401 Unauthorized")

    def meetings(self, year):
        raise OpenF1Error("OpenF1 request failed: 401 Unauthorized")


class PartialRateLimitedClient(FakeClient):
    def positions(self, session_key):
        raise OpenF1Error("OpenF1 request failed: 429 Too Many Requests")

    def laps(self, session_key):
        raise OpenF1Error("OpenF1 request failed: 429 Too Many Requests")

    def race_control(self, session_key):
        raise OpenF1Error("OpenF1 request failed: 429 Too Many Requests")

    def drivers(self, session_key):
        raise OpenF1Error("OpenF1 request failed: 429 Too Many Requests")


def test_dashboard_service_returns_partial_snapshot_when_openf1_is_rate_limited() -> None:
    service = DashboardService(client=RateLimitedClient(), standings_client=FakeStandingsClient(), venue_client=FakeVenueClient())

    snapshot = service.get_snapshot(refresh=True)

    assert isinstance(snapshot, DashboardSnapshot)
    assert snapshot.meeting is None
    assert snapshot.sessions == []
    assert snapshot.latest_positions == []
    assert snapshot.latest_laps == []
    assert snapshot.race_control == []
    assert snapshot.latest_results[0].status == "Race result"
    assert snapshot.generated_at_utc.tzinfo == timezone.utc


def test_dashboard_service_keeps_meeting_and_session_when_live_detail_calls_are_rate_limited() -> None:
    service = DashboardService(
        client=PartialRateLimitedClient(),
        standings_client=FakeStandingsClient(),
        venue_client=FakeVenueClient(),
        clock=lambda: datetime(2026, 5, 23, 14, 0, tzinfo=timezone.utc),
    )

    snapshot = service.get_snapshot(refresh=True)

    assert snapshot.meeting is not None
    assert snapshot.meeting.meeting_name == "Canadian Grand Prix"
    assert snapshot.sessions[0].session_name == "Sprint"
    assert snapshot.latest_positions == []
    assert snapshot.latest_laps == []
    assert snapshot.race_control == []
    assert snapshot.latest_results[0].status == "Race result"


def test_dashboard_service_returns_stale_cached_snapshot_when_refresh_is_rate_limited() -> None:
    cache: MemoryTTLCache[DashboardSnapshot] = MemoryTTLCache()
    warm_service = DashboardService(
        client=FakeClient(),
        standings_client=FakeStandingsClient(),
        venue_client=FakeVenueClient(),
        cache=cache,
        clock=lambda: datetime(2026, 5, 23, 14, 0, tzinfo=timezone.utc),
    )
    cached_snapshot = warm_service.get_snapshot(refresh=True)
    cache.set("dashboard:snapshot", cached_snapshot, ttl_seconds=0)

    rate_limited_service = DashboardService(
        client=RateLimitedClient(),
        standings_client=FakeStandingsClient(),
        venue_client=FakeVenueClient(),
        cache=cache,
        clock=lambda: datetime(2026, 5, 23, 14, 5, tzinfo=timezone.utc),
    )

    snapshot = rate_limited_service.get_snapshot(refresh=True)

    assert snapshot is cached_snapshot
    assert snapshot.meeting is not None
    assert snapshot.meeting.meeting_name == "Canadian Grand Prix"


def test_dashboard_service_restores_persisted_snapshot_when_live_api_is_locked(tmp_path) -> None:
    snapshot_cache_path = tmp_path / "dashboard-snapshot.json"

    warm_service = DashboardService(
        client=FakeClient(),
        standings_client=FakeStandingsClient(),
        venue_client=FakeVenueClient(),
        clock=lambda: datetime(2026, 5, 22, 20, 45, tzinfo=timezone.utc),
        snapshot_cache_path=str(snapshot_cache_path),
    )
    cached_snapshot = warm_service.get_snapshot(refresh=True)

    locked_service = DashboardService(
        client=AuthLockedClient(),
        standings_client=FakeStandingsClient(),
        venue_client=FakeVenueClient(),
        clock=lambda: datetime(2026, 5, 22, 20, 50, tzinfo=timezone.utc),
        snapshot_cache_path=str(snapshot_cache_path),
    )

    snapshot = locked_service.get_snapshot(refresh=True)

    assert snapshot.meeting is not None
    assert snapshot.meeting.meeting_name == cached_snapshot.meeting.meeting_name
    assert [session.session_name for session in snapshot.sessions] == ["Sprint Qualifying", "Sprint", "Grand Prix"]
    assert snapshot.venue is not None


def test_jolpica_client_wraps_timeout_error(monkeypatch) -> None:
    def raise_timeout(*args, **kwargs):
        raise TimeoutError("timed out")

    monkeypatch.setattr("f1dashboard.providers.jolpica.urlopen", raise_timeout)

    with pytest.raises(JolpicaError, match="timed out"):
        JolpicaClient().latest_race_results()


def test_dashboard_service_returns_fallback_results_when_jolpica_times_out() -> None:
    service = DashboardService(
        client=FakeClient(),
        standings_client=TimeoutStandingsClient(),
        venue_client=FakeVenueClient(),
    )

    snapshot = service.get_snapshot(refresh=True)

    assert snapshot.latest_results[0].driver_number == 12
    assert snapshot.latest_results[0].status == "Sprint Qualifying"


def test_dashboard_service_skips_venue_when_venue_requests_fail() -> None:
    service = DashboardService(
        client=FakeClient(),
        standings_client=FakeStandingsClient(),
        venue_client=BrokenVenueClient(),
    )

    snapshot = service.get_snapshot(refresh=True)

    assert snapshot.meeting is not None
    assert snapshot.venue is None
