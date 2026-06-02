from __future__ import annotations

from dataclasses import dataclass
from json import loads
from socket import timeout as SocketTimeout
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import urlopen


class JolpicaError(RuntimeError):
    pass


@dataclass(slots=True)
class JolpicaClient:
    base_url: str = "https://api.jolpi.ca/ergast/f1/"
    timeout_seconds: int = 20

    def _get_json(self, path: str) -> dict[str, Any]:
        url = urljoin(self.base_url, path)
        print(f"INFO: send api request to {url}")
        try:
            with urlopen(url, timeout=self.timeout_seconds) as response:
                raw = response.read().decode("utf-8")
                data = loads(raw)
        except HTTPError as exc:
            raise JolpicaError(f"Jolpica request failed: {exc.code} {exc.reason} for {url}") from exc
        except URLError as exc:
            raise JolpicaError(f"Jolpica request failed: {exc.reason} for {url}") from exc
        except (TimeoutError, SocketTimeout, OSError) as exc:
            raise JolpicaError(f"Jolpica request timed out for {url}") from exc

        if not isinstance(data, dict):
            raise JolpicaError(f"Jolpica returned unexpected payload for {url}")
        return data

    def driver_standings(self, season: str = "current") -> list[dict[str, Any]]:
        payload = self._get_json(f"{season}/driverStandings.json")
        return _extract_standings_list(payload, "DriverStandings")

    def constructor_standings(self, season: str = "current") -> list[dict[str, Any]]:
        payload = self._get_json(f"{season}/constructorStandings.json")
        return _extract_standings_list(payload, "ConstructorStandings")

    def current_circuits(self) -> list[dict[str, Any]]:
        payload = self._get_json("current/circuits.json")
        try:
            return payload["MRData"]["CircuitTable"]["Circuits"]
        except (KeyError, TypeError) as exc:
            raise JolpicaError("Jolpica circuit response is missing MRData.CircuitTable.Circuits") from exc

    def latest_race_results(self, season: str = "current") -> dict[str, Any] | None:
        payload = self._get_json(f"{season}/last/results.json")
        races = _extract_race_table(payload)
        return races[0] if races else None

    def latest_qualifying_results(self, season: str = "current") -> dict[str, Any] | None:
        payload = self._get_json(f"{season}/last/qualifying.json")
        races = _extract_race_table(payload)
        return races[0] if races else None


def _extract_race_table(payload: dict[str, Any]) -> list[dict[str, Any]]:
    try:
        races = payload["MRData"]["RaceTable"]["Races"]
    except (KeyError, TypeError) as exc:
        raise JolpicaError("Jolpica race response is missing MRData.RaceTable.Races") from exc
    if not isinstance(races, list):
        raise JolpicaError("Jolpica race response has invalid Races")
    return races


def _extract_standings_list(payload: dict[str, Any], key: str) -> list[dict[str, Any]]:
    try:
        standings_lists = payload["MRData"]["StandingsTable"]["StandingsLists"]
    except (KeyError, TypeError) as exc:
        raise JolpicaError("Jolpica standings response is missing MRData.StandingsTable.StandingsLists") from exc

    if not standings_lists:
        return []

    standings = standings_lists[0].get(key, [])
    if not isinstance(standings, list):
        raise JolpicaError(f"Jolpica standings response has invalid {key}")
    return standings
