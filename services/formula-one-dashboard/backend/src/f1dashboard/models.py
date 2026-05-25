from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(slots=True)
class Meeting:
    meeting_key: int
    meeting_name: str
    meeting_official_name: str | None
    location: str | None
    country_code: str | None
    country_name: str | None


@dataclass(slots=True)
class Session:
    session_key: int
    meeting_key: int
    session_name: str
    session_type: str
    date_start_utc: datetime
    date_end_utc: datetime | None = None


@dataclass(slots=True)
class PositionSample:
    date_utc: datetime
    session_key: int
    meeting_key: int
    driver_number: int
    position: int


@dataclass(slots=True)
class LapSample:
    meeting_key: int
    session_key: int
    driver_number: int
    lap_number: int
    date_start_utc: datetime | None = None
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class RaceControlMessage:
    meeting_key: int | None
    session_key: int | None
    date_utc: datetime
    category: str | None
    message: str


@dataclass(slots=True)
class ClassificationRow:
    position: int | None
    driver_number: int | None
    driver_name: str | None
    team_name: str | None
    points: float | None = None
    status: str | None = None


@dataclass(slots=True)
class WeatherForecastDay:
    date: str
    label: str
    summary: str
    is_wet: bool
    precipitation_probability_max: int | None = None
    precipitation_sum_mm: float | None = None
    rain_sum_mm: float | None = None
    showers_sum_mm: float | None = None
    snowfall_sum_mm: float | None = None
    temperature_max_c: float | None = None
    temperature_min_c: float | None = None


@dataclass(slots=True)
class VenueContext:
    circuit_name: str
    circuit_short_name: str | None = None
    circuit_image_url: str | None = None
    circuit_wiki_url: str | None = None
    track_map_svg: str | None = None
    track_length_km: float | None = None
    fastest_lap_seconds: float | None = None
    average_pit_stop_seconds: float | None = None
    weather_forecast: list[WeatherForecastDay] = field(default_factory=list)


@dataclass(slots=True)
class ChampionshipStandingRow:
    position: int | None
    competitor_name: str
    points: float
    wins: int | None = None
    gap: str | None = None


@dataclass(slots=True)
class DashboardSnapshot:
    meeting: Meeting | None
    sessions: list[Session]
    latest_positions: list[PositionSample]
    latest_laps: list[LapSample]
    race_control: list[RaceControlMessage]
    latest_results: list[ClassificationRow]
    driver_standings: list[ChampionshipStandingRow]
    constructor_standings: list[ChampionshipStandingRow]
    generated_at_utc: datetime
    venue: VenueContext | None = None
