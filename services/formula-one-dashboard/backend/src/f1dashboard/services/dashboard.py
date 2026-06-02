from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable

from f1dashboard.cache import MemoryTTLCache
from f1dashboard.models import (
    ChampionshipStandingRow,
    ClassificationRow,
    DashboardSnapshot,
    LapSample,
    Meeting,
    PositionSample,
    RaceControlMessage,
    Session,
    VenueContext,
    WeatherForecastDay,
)
from f1dashboard.providers.jolpica import JolpicaClient, JolpicaError
from f1dashboard.providers.openf1 import OpenF1Client, OpenF1Error, parse_utc_timestamp
from f1dashboard.providers.venue import VenueClient, VenueError


class DashboardService:
    def __init__(
        self,
        client: OpenF1Client | None = None,
        standings_client: JolpicaClient | None = None,
        venue_client: VenueClient | None = None,
        cache: MemoryTTLCache[DashboardSnapshot] | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self.client = client or OpenF1Client()
        self.standings_client = standings_client or JolpicaClient()
        self.venue_client = venue_client or VenueClient()
        self.cache = cache or MemoryTTLCache[DashboardSnapshot]()
        self.clock = clock or (lambda: datetime.now(timezone.utc))

    def get_snapshot(self, refresh: bool = False) -> DashboardSnapshot:
        cache_key = "dashboard:snapshot"
        if not refresh:
            cached = self.cache.get(cache_key)
            if cached is not None:
                return cached

        critical_provider_error = False
        latest_session_raw = None

        try:
            meeting_raw = self._next_meeting_row()
        except OpenF1Error:
            meeting_raw = None
            critical_provider_error = True

        if meeting_raw is None and latest_session_raw is not None:
            # Last resort only: `latest` is the latest completed/current meeting,
            # not the next scheduled one. Use it only when the schedule lookup fails.
            try:
                meeting_raw = self.client.latest_meeting()
            except OpenF1Error:
                meeting_raw = None
                critical_provider_error = True

        if critical_provider_error:
            stale_snapshot = self.cache.get_stale(cache_key)
            if stale_snapshot is not None and self._snapshot_has_future_session(stale_snapshot):
                return stale_snapshot

        upcoming_session_rows = self._upcoming_session_rows(meeting_raw)
        session_rows = upcoming_session_rows

        meeting = self._meeting_from_raw(meeting_raw) if meeting_raw else None
        sessions = [self._session_from_raw(row) for row in session_rows]

        # The dashboard is intentionally focused on the next session, venue,
        # the latest qualifying/race result, and the two championship tables.
        # Avoid fetching unused live telemetry/race-control feeds here.
        latest_positions: list[PositionSample] = []
        latest_laps: list[LapSample] = []
        race_control: list[RaceControlMessage] = []
        latest_results = self._latest_completed_results(latest_session_raw)

        driver_standings = self._driver_standings()
        constructor_standings = self._constructor_standings()
        venue = self._venue_context(meeting_raw, latest_session_raw, latest_laps)

        snapshot = DashboardSnapshot(
            meeting=meeting,
            sessions=sessions,
            latest_positions=latest_positions,
            latest_laps=latest_laps,
            race_control=race_control,
            latest_results=latest_results,
            driver_standings=driver_standings,
            constructor_standings=constructor_standings,
            venue=venue,
            generated_at_utc=self.clock(),
        )
        self.cache.set(cache_key, snapshot, ttl_seconds=600)
        return snapshot

    def _snapshot_has_future_session(self, snapshot: DashboardSnapshot) -> bool:
        now = _as_utc(self.clock())
        return any(session.date_start_utc > now for session in snapshot.sessions)

    def _next_meeting_row(self) -> dict[str, Any] | None:
        now = _as_utc(self.clock())
        candidate_rows: list[dict[str, Any]] = []
        years = [now.year, now.year + 1]
        for year in years:
            try:
                candidate_rows.extend(self.client.meetings(year))
            except AttributeError:
                # Compatibility for tests/older clients: fall back to the old latest endpoint.
                latest = self.client.latest_meeting()
                return latest if self._meeting_has_future_time(latest, now) else None
            except OpenF1Error:
                if not candidate_rows:
                    raise

            future_rows = [row for row in candidate_rows if self._meeting_has_future_time(row, now)]
            if future_rows:
                return sorted(future_rows, key=lambda row: parse_utc_timestamp(row.get("date_start")) or datetime.max.replace(tzinfo=timezone.utc))[0]

        return None

    def _meeting_has_future_time(self, row: dict[str, Any] | None, now: datetime) -> bool:
        if not row or row.get("is_cancelled") is True:
            return False
        end = parse_utc_timestamp(row.get("date_end"))
        start = parse_utc_timestamp(row.get("date_start"))
        if end is not None:
            return end > now
        return start is not None and start > now

    def _meeting_from_raw(self, raw: dict[str, Any]) -> Meeting:
        return Meeting(
            meeting_key=int(raw["meeting_key"]),
            meeting_name=str(raw.get("meeting_name", "")),
            meeting_official_name=raw.get("meeting_official_name"),
            location=raw.get("location"),
            country_code=raw.get("country_code"),
            country_name=raw.get("country_name"),
        )

    def _session_from_raw(self, raw: dict[str, Any]) -> Session:
        start = parse_utc_timestamp(raw.get("date_start")) or self.clock()
        end = parse_utc_timestamp(raw.get("date_end"))
        return Session(
            session_key=int(raw["session_key"]),
            meeting_key=int(raw["meeting_key"]),
            session_name=str(raw.get("session_name", raw.get("session_type", "Session"))),
            session_type=str(raw.get("session_type", "unknown")),
            date_start_utc=start,
            date_end_utc=end,
        )

    def _upcoming_session_rows(self, meeting_raw: dict[str, Any] | None) -> list[dict[str, Any]]:
        if not meeting_raw:
            return []

        try:
            rows = self.client.sessions(int(meeting_raw["meeting_key"]))
        except (KeyError, OpenF1Error):
            rows = []

        now = _as_utc(self.clock())
        future_rows = [row for row in rows if (parse_utc_timestamp(row.get("date_start")) or datetime.min.replace(tzinfo=timezone.utc)) > now]
        if not future_rows:
            future_rows = self._future_session_rows_for_meeting(meeting_raw, now)
        return sorted(future_rows, key=lambda row: parse_utc_timestamp(row.get("date_start")) or datetime.max.replace(tzinfo=timezone.utc))

    def _future_session_rows_for_meeting(self, meeting_raw: dict[str, Any], now: datetime) -> list[dict[str, Any]]:
        meeting_key = _optional_int(meeting_raw.get("meeting_key"))
        if meeting_key is None:
            return []
        try:
            rows = self.client.future_sessions(now.isoformat())
        except (AttributeError, OpenF1Error):
            return []
        return [
            row
            for row in rows
            if _optional_int(row.get("meeting_key")) == meeting_key
            and (parse_utc_timestamp(row.get("date_start")) or datetime.min.replace(tzinfo=timezone.utc)) > now
        ]

    def _position_rows(self, session_raw: dict[str, Any] | None) -> list[dict[str, Any]]:
        if not session_raw:
            return []
        try:
            return self.client.positions(int(session_raw["session_key"]))
        except (KeyError, OpenF1Error):
            return []

    def _latest_positions(self, session_raw: dict[str, Any] | None, rows: list[dict[str, Any]] | None = None) -> list[PositionSample]:
        if not session_raw:
            return []
        session_key = int(session_raw["session_key"])
        meeting_key = int(session_raw["meeting_key"])
        if rows is None:
            rows = self._position_rows(session_raw)
        parsed: list[PositionSample] = []
        for row in rows:
            parsed.append(
                PositionSample(
                    date_utc=parse_utc_timestamp(row["date"]) or self.clock(),
                    session_key=session_key,
                    meeting_key=meeting_key,
                    driver_number=int(row["driver_number"]),
                    position=int(row["position"]),
                )
            )
        return parsed[:20]

    def _latest_laps(self, session_raw: dict[str, Any] | None) -> list[LapSample]:
        if not session_raw:
            return []
        session_key = int(session_raw["session_key"])
        meeting_key = int(session_raw["meeting_key"])
        try:
            rows = self.client.laps(session_key)
        except OpenF1Error:
            return []
        parsed: list[LapSample] = []
        for row in rows[:20]:
            payload = dict(row)
            parsed.append(
                LapSample(
                    meeting_key=meeting_key,
                    session_key=session_key,
                    driver_number=int(row["driver_number"]),
                    lap_number=int(row["lap_number"]),
                    date_start_utc=parse_utc_timestamp(row.get("date_start")),
                    payload=payload,
                )
            )
        return parsed

    def _latest_race_control(self, session_raw: dict[str, Any] | None) -> list[RaceControlMessage]:
        if not session_raw:
            return []
        session_key = int(session_raw["session_key"])
        meeting_key = int(session_raw["meeting_key"])
        try:
            rows = self.client.race_control(session_key)
        except OpenF1Error:
            return []
        parsed: list[RaceControlMessage] = []
        for row in rows[:30]:
            parsed.append(
                RaceControlMessage(
                    meeting_key=meeting_key,
                    session_key=session_key,
                    date_utc=parse_utc_timestamp(row["date"]) or self.clock(),
                    category=row.get("category"),
                    message=str(row.get("message", "")),
                )
            )
        return parsed

    def _latest_completed_results(self, fallback_session_raw: dict[str, Any] | None = None) -> list[ClassificationRow]:
        race_result: dict[str, Any] | None = None
        qualifying_result: dict[str, Any] | None = None
        try:
            race_result = self.standings_client.latest_race_results()
        except (AttributeError, JolpicaError):
            race_result = None
        try:
            qualifying_result = self.standings_client.latest_qualifying_results()
        except (AttributeError, JolpicaError):
            qualifying_result = None

        selected = self._newer_jolpica_event(race_result, qualifying_result)
        if selected is race_result and race_result is not None:
            rows = race_result.get("Results", [])
            parsed = [self._classification_from_jolpica_race_row(row, "Race result") for row in rows]
            return [row for row in parsed if row is not None]
        if selected is qualifying_result and qualifying_result is not None:
            rows = qualifying_result.get("QualifyingResults", [])
            parsed = [self._classification_from_jolpica_qualifying_row(row, "Qualifying result") for row in rows]
            return [row for row in parsed if row is not None]

        # Fallback for tests/local development when Jolpica does not provide result endpoints.
        return self._latest_results(fallback_session_raw)

    def _newer_jolpica_event(
        self,
        race_result: dict[str, Any] | None,
        qualifying_result: dict[str, Any] | None,
    ) -> dict[str, Any] | None:
        if race_result is None:
            return qualifying_result
        if qualifying_result is None:
            return race_result

        race_time = _jolpica_event_datetime(race_result)
        qualifying_time = _jolpica_event_datetime(qualifying_result)
        if race_time is None:
            return qualifying_result
        if qualifying_time is None:
            return race_result
        return qualifying_result if qualifying_time > race_time else race_result

    def _classification_from_jolpica_race_row(self, row: dict[str, Any], status: str) -> ClassificationRow | None:
        driver = row.get("Driver", {})
        constructor = row.get("Constructor", {})
        driver_number = _optional_int(row.get("number") or driver.get("permanentNumber"))
        return ClassificationRow(
            position=_optional_int(row.get("position")),
            driver_number=driver_number,
            driver_name=_jolpica_driver_name(driver, driver_number),
            team_name=constructor.get("name"),
            points=_optional_float(row.get("points")),
            status=status,
        )

    def _classification_from_jolpica_qualifying_row(self, row: dict[str, Any], status: str) -> ClassificationRow | None:
        driver = row.get("Driver", {})
        constructor = row.get("Constructor", {})
        driver_number = _optional_int(row.get("number") or driver.get("permanentNumber"))
        best_time = row.get("Q3") or row.get("Q2") or row.get("Q1")
        return ClassificationRow(
            position=_optional_int(row.get("position")),
            driver_number=driver_number,
            driver_name=_jolpica_driver_name(driver, driver_number),
            team_name=constructor.get("name"),
            points=None,
            status=f"{status} · {best_time}" if best_time else status,
        )

    def _latest_results(self, session_raw: dict[str, Any] | None, position_rows: list[dict[str, Any]] | None = None) -> list[ClassificationRow]:
        if not session_raw:
            return []

        session_key = int(session_raw["session_key"])
        if position_rows is None:
            position_rows = self._position_rows(session_raw)
        try:
            driver_rows = self.client.drivers(session_key)
        except OpenF1Error:
            driver_rows = []

        latest_by_driver: dict[int, dict[str, Any]] = {}
        for row in position_rows:
            driver_number = _optional_int(row.get("driver_number"))
            if driver_number is None:
                continue
            row_date = parse_utc_timestamp(row.get("date")) or datetime.min.replace(tzinfo=timezone.utc)
            previous = latest_by_driver.get(driver_number)
            previous_date = parse_utc_timestamp(previous.get("date")) if previous else None
            if previous is None or previous_date is None or row_date >= previous_date:
                latest_by_driver[driver_number] = row

        drivers_by_number = {
            int(row["driver_number"]): row
            for row in driver_rows
            if row.get("driver_number") is not None
        }

        session_name = str(session_raw.get("session_name", session_raw.get("session_type", "Session")))
        parsed: list[ClassificationRow] = []
        sorted_positions = sorted(latest_by_driver.values(), key=lambda row: _optional_int(row.get("position")) or 999)
        for row in sorted_positions:
            driver_number = _optional_int(row.get("driver_number"))
            if driver_number is None:
                continue
            driver = drivers_by_number.get(driver_number, {})
            parsed.append(
                ClassificationRow(
                    position=_optional_int(row.get("position")),
                    driver_number=driver_number,
                    driver_name=_driver_display_name(driver, driver_number),
                    team_name=driver.get("team_name"),
                    points=None,
                    status=session_name,
                )
            )
        return parsed

    def _driver_standings(self) -> list[ChampionshipStandingRow]:
        try:
            rows = self.standings_client.driver_standings()
        except JolpicaError:
            return []

        parsed: list[ChampionshipStandingRow] = []
        for row in rows:
            driver = row.get("Driver", {})
            given_name = str(driver.get("givenName", "")).strip()
            family_name = str(driver.get("familyName", "")).strip()
            competitor_name = " ".join(part for part in [given_name, family_name] if part) or str(driver.get("driverId", "Unknown driver"))
            parsed.append(
                ChampionshipStandingRow(
                    position=_optional_int(row.get("position")),
                    competitor_name=competitor_name,
                    points=_float_or_zero(row.get("points")),
                    wins=_optional_int(row.get("wins")),
                    gap=None,
                )
            )
        return parsed

    def _constructor_standings(self) -> list[ChampionshipStandingRow]:
        try:
            rows = self.standings_client.constructor_standings()
        except JolpicaError:
            return []

        parsed: list[ChampionshipStandingRow] = []
        for row in rows:
            constructor = row.get("Constructor", {})
            competitor_name = str(constructor.get("name") or constructor.get("constructorId") or "Unknown constructor")
            parsed.append(
                ChampionshipStandingRow(
                    position=_optional_int(row.get("position")),
                    competitor_name=competitor_name,
                    points=_float_or_zero(row.get("points")),
                    wins=_optional_int(row.get("wins")),
                    gap=None,
                )
            )
        return parsed


    def _venue_context(
        self,
        meeting_raw: dict[str, Any] | None,
        session_raw: dict[str, Any] | None,
        latest_laps: list[LapSample],
    ) -> VenueContext | None:
        if not meeting_raw:
            return None

        try:
            circuit_details = self.venue_client.resolve_circuit(meeting_raw)
        except VenueError:
            return None
        if not circuit_details:
            return None

        fastest_lap_seconds = self._fastest_lap_seconds(latest_laps)
        average_pit_stop_seconds = self._average_pit_stop_seconds(self._pit_rows(session_raw))

        weather_forecast: list[WeatherForecastDay] = []
        latitude = circuit_details.get("latitude")
        longitude = circuit_details.get("longitude")
        start_date = parse_utc_timestamp(meeting_raw.get("date_start"))
        end_date = parse_utc_timestamp(meeting_raw.get("date_end")) or start_date
        if latitude is not None and longitude is not None and start_date and end_date:
            try:
                forecast_rows = self.venue_client.weather_forecast(latitude, longitude, start_date.date(), end_date.date())
                weather_forecast = [WeatherForecastDay(**row) for row in forecast_rows]
            except VenueError:
                weather_forecast = []

        return VenueContext(
            circuit_name=str(circuit_details.get("circuit_name") or "Track"),
            circuit_short_name=circuit_details.get("circuit_short_name"),
            circuit_image_url=circuit_details.get("circuit_image_url"),
            circuit_wiki_url=circuit_details.get("circuit_wiki_url"),
            track_map_svg=circuit_details.get("track_map_svg"),
            track_length_km=circuit_details.get("track_length_km"),
            fastest_lap_seconds=fastest_lap_seconds,
            average_pit_stop_seconds=average_pit_stop_seconds,
            weather_forecast=weather_forecast,
        )

    def _pit_rows(self, session_raw: dict[str, Any] | None) -> list[dict[str, Any]]:
        if not session_raw:
            return []
        try:
            return self.client.pit(int(session_raw["session_key"]))
        except (AttributeError, KeyError, OpenF1Error):
            return []

    def _fastest_lap_seconds(self, latest_laps: list[LapSample]) -> float | None:
        lap_durations = [
            float(duration)
            for duration in (row.payload.get("lap_duration") for row in latest_laps)
            if isinstance(duration, (int, float))
        ]
        if not lap_durations:
            return None
        return min(lap_durations)

    def _average_pit_stop_seconds(self, pit_rows: list[dict[str, Any]]) -> float | None:
        durations = []
        for row in pit_rows:
            value = row.get("pit_duration")
            if value in (None, ""):
                value = row.get("stop_duration")
            if value in (None, ""):
                value = row.get("lane_duration")
            duration = _optional_float(value)
            if duration is None:
                continue
            durations.append(duration / 100.0 if duration > 100 else duration)
        if not durations:
            return None
        return sum(durations) / len(durations)


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _jolpica_event_datetime(event: dict[str, Any]) -> datetime | None:
    date = str(event.get("date") or "").strip()
    time = str(event.get("time") or "00:00:00Z").strip()
    if not date:
        return None
    return parse_utc_timestamp(f"{date}T{time}")


def _jolpica_driver_name(driver: dict[str, Any], driver_number: int | None) -> str:
    given_name = str(driver.get("givenName", "")).strip()
    family_name = str(driver.get("familyName", "")).strip()
    name = " ".join(part for part in [given_name, family_name] if part)
    if name:
        return name
    driver_id = str(driver.get("driverId", "")).strip()
    if driver_id:
        return driver_id
    return f"Driver {driver_number}" if driver_number is not None else "Unknown driver"


def _driver_display_name(driver: dict[str, Any], driver_number: int) -> str:
    full_name = str(driver.get("full_name", "")).strip()
    if full_name:
        return full_name

    first_name = str(driver.get("first_name", "")).strip()
    last_name = str(driver.get("last_name", "")).strip()
    name = " ".join(part for part in [first_name, last_name] if part)
    if name:
        return name

    broadcast_name = str(driver.get("broadcast_name", "")).strip()
    if broadcast_name:
        return broadcast_name

    acronym = str(driver.get("name_acronym", "")).strip()
    if acronym:
        return acronym

    return f"Driver {driver_number}"


def _optional_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _optional_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _float_or_zero(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0
