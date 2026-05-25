from f1dashboard.providers.openf1 import parse_utc_timestamp


def test_parse_utc_timestamp_normalizes_timezone() -> None:
    parsed = parse_utc_timestamp("2026-05-22T20:30:00+00:00")
    assert parsed is not None
    assert parsed.tzinfo is not None
    assert parsed.utcoffset().total_seconds() == 0
