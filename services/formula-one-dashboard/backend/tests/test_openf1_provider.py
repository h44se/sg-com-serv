import pytest

from f1dashboard.providers.openf1 import OpenF1Client, OpenF1Error, parse_utc_timestamp


def test_parse_utc_timestamp_normalizes_timezone() -> None:
    parsed = parse_utc_timestamp("2026-05-22T20:30:00+00:00")
    assert parsed is not None
    assert parsed.tzinfo is not None
    assert parsed.utcoffset().total_seconds() == 0


def test_openf1_client_wraps_timeout_error(monkeypatch) -> None:
    def raise_timeout(*args, **kwargs):
        raise TimeoutError("timed out")

    monkeypatch.setattr("f1dashboard.providers.openf1.urlopen", raise_timeout)

    with pytest.raises(OpenF1Error, match="timed out"):
        OpenF1Client().meetings(2026)
