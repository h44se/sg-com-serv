from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from html import unescape
from json import loads
from math import hypot
from socket import timeout as SocketTimeout
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlparse
from urllib.request import Request, urlopen
import re
import unicodedata

from f1dashboard.providers.jolpica import JolpicaClient, JolpicaError


class VenueError(RuntimeError):
    pass


@dataclass(slots=True)
class VenueClient:
    circuits_client: JolpicaClient | None = None
    timeout_seconds: int = 20

    def __post_init__(self) -> None:
        if self.circuits_client is None:
            self.circuits_client = JolpicaClient(timeout_seconds=self.timeout_seconds)

    def resolve_circuit(self, meeting_raw: dict[str, Any]) -> dict[str, Any] | None:
        circuit_info_url = meeting_raw.get("circuit_info_url")
        circuit_image_url = meeting_raw.get("circuit_image")
        circuit_short_name = str(meeting_raw.get("circuit_short_name", "")).strip() or None
        circuit_name = circuit_short_name or str(meeting_raw.get("meeting_name", "Track")).strip() or "Track"

        latlon = self._lookup_latlon(meeting_raw)
        track_map_svg = self._track_map_svg(circuit_info_url) if circuit_info_url else None
        circuit_length_km = self._circuit_length_km(latlon.get("wiki_url")) if latlon.get("wiki_url") else None

        return {
            "circuit_name": circuit_name,
            "circuit_short_name": circuit_short_name,
            "circuit_image_url": circuit_image_url,
            "circuit_wiki_url": latlon.get("wiki_url"),
            "track_map_svg": track_map_svg,
            "track_length_km": circuit_length_km,
            "latitude": latlon.get("latitude"),
            "longitude": latlon.get("longitude"),
        }

    def weather_forecast(self, latitude: float, longitude: float, start_date: date, end_date: date) -> list[dict[str, Any]]:
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "daily": ",".join(
                [
                    "weather_code",
                    "temperature_2m_max",
                    "temperature_2m_min",
                    "precipitation_probability_max",
                    "precipitation_sum",
                    "rain_sum",
                    "showers_sum",
                    "snowfall_sum",
                ]
            ),
            "timezone": "UTC",
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
        }
        data = self._get_json("https://api.open-meteo.com/v1/forecast", params=params)
        daily = data.get("daily", {}) if isinstance(data, dict) else {}
        times = daily.get("time", []) if isinstance(daily, dict) else []
        result: list[dict[str, Any]] = []
        for index, day_iso in enumerate(times):
            if day_iso < start_date.isoformat() or day_iso > end_date.isoformat():
                continue
            weather_code = _optional_int(_pick(daily, "weather_code", index))
            precipitation_probability_max = _optional_int(_pick(daily, "precipitation_probability_max", index))
            precipitation_sum = _optional_float(_pick(daily, "precipitation_sum", index))
            rain_sum = _optional_float(_pick(daily, "rain_sum", index))
            showers_sum = _optional_float(_pick(daily, "showers_sum", index))
            snowfall_sum = _optional_float(_pick(daily, "snowfall_sum", index))
            temperature_max = _optional_float(_pick(daily, "temperature_2m_max", index))
            temperature_min = _optional_float(_pick(daily, "temperature_2m_min", index))
            result.append(
                {
                    "date": day_iso,
                    "label": _weekday_label(day_iso),
                    "summary": _weather_summary(weather_code, precipitation_probability_max, precipitation_sum),
                    "is_wet": _is_wet(weather_code, precipitation_probability_max, precipitation_sum, rain_sum, showers_sum, snowfall_sum),
                    "precipitation_probability_max": precipitation_probability_max,
                    "precipitation_sum_mm": precipitation_sum,
                    "rain_sum_mm": rain_sum,
                    "showers_sum_mm": showers_sum,
                    "snowfall_sum_mm": snowfall_sum,
                    "temperature_max_c": temperature_max,
                    "temperature_min_c": temperature_min,
                }
            )
        return result

    def _lookup_latlon(self, meeting_raw: dict[str, Any]) -> dict[str, Any]:
        try:
            circuits = self.circuits_client.current_circuits() if self.circuits_client else []
        except JolpicaError:
            circuits = []

        candidates = [
            meeting_raw.get("circuit_short_name"),
            meeting_raw.get("location"),
            meeting_raw.get("country_name"),
            meeting_raw.get("meeting_name"),
        ]
        normalized_candidates = [normalized for candidate in candidates if (normalized := _normalize(candidate))]
        for circuit in circuits:
            location = circuit.get("Location", {}) if isinstance(circuit, dict) else {}
            circuit_candidates = [
                circuit.get("circuitName"),
                location.get("locality"),
                location.get("country"),
                circuit.get("circuitId"),
            ]
            normalized_circuit = [normalized for candidate in circuit_candidates if (normalized := _normalize(candidate))]
            if any(candidate == circuit_value for candidate in normalized_candidates for circuit_value in normalized_circuit):
                return {
                    "latitude": _optional_float(location.get("lat")),
                    "longitude": _optional_float(location.get("long")),
                    "wiki_url": circuit.get("url"),
                }

        for circuit in circuits:
            location = circuit.get("Location", {}) if isinstance(circuit, dict) else {}
            circuit_values = " ".join(
                part for part in [str(circuit.get("circuitName", "")), str(location.get("locality", "")), str(location.get("country", ""))] if part
            )
            if any(candidate and candidate in _normalize(circuit_values) for candidate in normalized_candidates):
                return {
                    "latitude": _optional_float(location.get("lat")),
                    "longitude": _optional_float(location.get("long")),
                    "wiki_url": circuit.get("url"),
                }

        return {"latitude": None, "longitude": None, "wiki_url": None}

    def _track_map_svg(self, circuit_info_url: str) -> str | None:
        try:
            data = self._get_json(circuit_info_url, headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"})
        except VenueError:
            return None
        if not isinstance(data, dict):
            return None
        x_values = data.get("x") or []
        y_values = data.get("y") or []
        if not x_values or not y_values or len(x_values) != len(y_values):
            return None

        points = list(zip(x_values, y_values))
        if not points:
            return None
        step = max(len(points) // 220, 1)
        sampled = points[::step]
        xs = [float(point[0]) for point in sampled]
        ys = [float(point[1]) for point in sampled]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        width = max(max_x - min_x, 1.0)
        height = max(max_y - min_y, 1.0)
        pad = 14
        view_w = 180
        view_h = 120
        drawable_w = view_w - pad * 2
        drawable_h = view_h - pad * 2
        scale = min(drawable_w / width, drawable_h / height)
        offset_x = pad + (drawable_w - width * scale) / 2
        offset_y = pad + (drawable_h - height * scale) / 2

        def tx(x: float) -> float:
            return (x - min_x) * scale + offset_x

        def ty(y: float) -> float:
            return (max_y - y) * scale + offset_y

        path = " ".join([
            f"M {tx(sampled[0][0]):.1f} {ty(sampled[0][1]):.1f}",
            *[f"L {tx(x):.1f} {ty(y):.1f}" for x, y in sampled[1:]],
        ])
        return (
            '<svg viewBox="0 0 180 120" role="img" aria-label="Circuit minimap" xmlns="http://www.w3.org/2000/svg">'
            '<rect x="0" y="0" width="180" height="120" rx="16" fill="#0b0b0d"/>'
            '<path d="{path}" fill="none" stroke="#ff1e2d" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>'
            '<circle cx="{start_x}" cy="{start_y}" r="4.2" fill="#ffffff" stroke="#ff1e2d" stroke-width="2"/>'
            '<circle cx="{end_x}" cy="{end_y}" r="4.2" fill="#ff1e2d" stroke="#ffffff" stroke-width="1.5"/>'
            '</svg>'
        ).format(
            path=path,
            start_x=f"{tx(sampled[0][0]):.1f}",
            start_y=f"{ty(sampled[0][1]):.1f}",
            end_x=f"{tx(sampled[-1][0]):.1f}",
            end_y=f"{ty(sampled[-1][1]):.1f}",
        )

    def _circuit_length_km(self, wiki_url: str | None) -> float | None:
        if not wiki_url:
            return None
        page = urlparse(wiki_url).path.rsplit("/", 1)[-1]
        if not page:
            return None
        api_url = "https://en.wikipedia.org/w/api.php"
        try:
            html = self._get_json(api_url, params={"action": "parse", "page": page, "prop": "text", "format": "json", "formatversion": 2}, headers={"User-Agent": "Mozilla/5.0"})
        except VenueError:
            return None
        text = html.get("parse", {}).get("text", "") if isinstance(html, dict) else ""
        if not text:
            return None
        match = re.search(r'<th[^>]*>Length</th><td class="infobox-data">([0-9.,]+)\s*km', text)
        if not match:
            return None
        try:
            return float(match.group(1).replace(",", "")) if "," in match.group(1) and "." not in match.group(1) else float(match.group(1).replace(",", "."))
        except ValueError:
            return None

    def _get_json(self, url: str, params: dict[str, Any] | None = None, headers: dict[str, str] | None = None) -> Any:
        if params:
            query = "&".join(f"{quote(str(key))}={quote(str(value))}" for key, value in params.items())
            url = f"{url}?{query}"
        request = Request(url, headers=headers or {})
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                return loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            raise VenueError(f"Venue request failed: {exc.code} {exc.reason} for {url}") from exc
        except URLError as exc:
            raise VenueError(f"Venue request failed: {exc.reason} for {url}") from exc
        except (TimeoutError, SocketTimeout, OSError) as exc:
            raise VenueError(f"Venue request timed out for {url}") from exc


def _normalize(value: Any) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(char for char in text if not unicodedata.combining(char))
    return re.sub(r"[^a-z0-9]+", "", text.lower())


def _optional_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def _optional_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _pick(data: dict[str, Any], key: str, index: int) -> Any:
    value = data.get(key, [])
    if isinstance(value, list) and index < len(value):
        return value[index]
    return None


def _weekday_label(day_iso: str) -> str:
    return datetime.fromisoformat(day_iso).strftime("%a")


def _weather_summary(
    weather_code: int | None,
    precipitation_probability_max: int | None,
    precipitation_sum: float | None,
) -> str:
    if weather_code is not None:
        if weather_code in {71, 73, 75, 77, 85, 86}:
            return "Snow"
        if weather_code in {51, 53, 55, 61, 63, 65, 66, 67, 80, 81, 82, 95, 96, 99}:
            return "Wet"
        if weather_code in {0, 1}:
            return "Dry"
    if (precipitation_probability_max or 0) >= 50 or (precipitation_sum or 0.0) >= 1.0:
        return "Wet"
    return "Dry"


def _is_wet(
    weather_code: int | None,
    precipitation_probability_max: int | None,
    precipitation_sum: float | None,
    rain_sum: float | None,
    showers_sum: float | None,
    snowfall_sum: float | None,
) -> bool:
    if weather_code is not None:
        if weather_code in {51, 53, 55, 61, 63, 65, 66, 67, 80, 81, 82, 95, 96, 99, 71, 73, 75, 77, 85, 86}:
            return True
        if weather_code in {0, 1, 2}:
            return False
    wet_score = sum(
        value or 0.0
        for value in [
            precipitation_sum,
            rain_sum,
            showers_sum,
            snowfall_sum,
        ]
    )
    return (precipitation_probability_max or 0) >= 50 or wet_score >= 1.0
