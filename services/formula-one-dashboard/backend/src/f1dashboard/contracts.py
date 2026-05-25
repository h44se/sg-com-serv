from __future__ import annotations

from f1dashboard.models import (
    ChampionshipStandingRow,
    ClassificationRow,
    DashboardSnapshot,
    LapSample,
    Meeting,
    PositionSample,
    RaceControlMessage,
    Session,
)

API_ENDPOINTS = {
    "dashboard": "/api/dashboard",
    "next_race": "/api/next-race",
    "schedule_next": "/api/schedule/next",
    "countdown": "/api/countdown",
    "results_latest": "/api/results/latest",
    "standings_drivers": "/api/standings/drivers",
    "standings_constructors": "/api/standings/constructors",
}
