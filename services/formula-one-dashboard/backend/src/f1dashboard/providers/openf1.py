from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from json import loads
from socket import timeout as SocketTimeout
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class OpenF1Error(RuntimeError):
    pass


@dataclass(slots=True)
class OpenF1Client:
    base_url: str = "https://api.openf1.org"
    timeout_seconds: int = 20

    def _get_json(self, path: str, params: dict[str, Any] | None = None) -> Any:
        query = f"?{urlencode(params)}" if params else ""
        url = f"{self.base_url}{path}{query}"
        print(f"INFO: send api request to {url}")
        try:
            with urlopen(url, timeout=self.timeout_seconds) as response:
                raw = response.read().decode("utf-8")
                return loads(raw)
        except HTTPError as exc:
            raise OpenF1Error(f"OpenF1 request failed: {exc.code} {exc.reason} for {url}") from exc
        except URLError as exc:
            raise OpenF1Error(f"OpenF1 request failed: {exc.reason} for {url}") from exc
        except (TimeoutError, SocketTimeout, OSError) as exc:
            raise OpenF1Error(f"OpenF1 request timed out for {url}") from exc

    def latest_meeting(self) -> dict[str, Any] | None:
        data = self._get_json("/v1/meetings", {"meeting_key": "latest"})
        return data[0] if data else None

    def latest_session(self) -> dict[str, Any] | None:
        data = self._get_json("/v1/sessions", {"session_key": "latest"})
        return data[0] if data else None

    def meetings(self, year: int) -> list[dict[str, Any]]:
        return self._get_json("/v1/meetings", {"year": year})

    def sessions(self, meeting_key: int) -> list[dict[str, Any]]:
        return self._get_json("/v1/sessions", {"meeting_key": meeting_key})

    def future_sessions(self, since_utc_iso: str) -> list[dict[str, Any]]:
        return self._get_json("/v1/sessions", {"date_start>=": since_utc_iso})

    def positions(self, session_key: int) -> list[dict[str, Any]]:
        return self._get_json("/v1/position", {"session_key": session_key})

    def drivers(self, session_key: int) -> list[dict[str, Any]]:
        return self._get_json("/v1/drivers", {"session_key": session_key})

    def laps(self, session_key: int) -> list[dict[str, Any]]:
        return self._get_json("/v1/laps", {"session_key": session_key})

    def stints(self, session_key: int) -> list[dict[str, Any]]:
        return self._get_json("/v1/stints", {"session_key": session_key})

    def pit(self, session_key: int) -> list[dict[str, Any]]:
        return self._get_json("/v1/pit", {"session_key": session_key})

    def race_control(self, session_key: int) -> list[dict[str, Any]]:
        return self._get_json("/v1/race_control", {"session_key": session_key})


def parse_utc_timestamp(value: str | None) -> datetime | None:
    if not value:
        return None
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)
