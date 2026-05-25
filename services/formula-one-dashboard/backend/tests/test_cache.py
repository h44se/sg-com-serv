from __future__ import annotations

from datetime import datetime, timezone

from f1dashboard.cache import MemoryTTLCache
from f1dashboard.models import DashboardSnapshot


def test_ttl_cache_expires_entries() -> None:
    cache: MemoryTTLCache[DashboardSnapshot] = MemoryTTLCache()
    snapshot = DashboardSnapshot(
        meeting=None,
        sessions=[],
        latest_positions=[],
        latest_laps=[],
        race_control=[],
        latest_results=[],
        driver_standings=[],
        constructor_standings=[],
        generated_at_utc=datetime.now(timezone.utc),
    )
    cache.set("key", snapshot, ttl_seconds=0)
    assert cache.get("key") is None
