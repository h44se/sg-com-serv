from datetime import date

from f1dashboard.providers.venue import VenueClient


def test_weather_forecast_requests_meeting_date_range() -> None:
    requested: dict[str, object] = {}

    class StubVenueClient(VenueClient):
        def _get_json(self, url, params=None, headers=None):
            requested["url"] = url
            requested["params"] = params or {}
            return {
                "daily": {
                    "time": ["2026-06-05", "2026-06-06", "2026-06-07"],
                    "weather_code": [1, 61, 3],
                    "temperature_2m_max": [25.0, 22.0, 24.0],
                    "temperature_2m_min": [19.0, 18.0, 20.0],
                    "precipitation_probability_max": [10, 70, 20],
                    "precipitation_sum": [0.0, 4.5, 0.2],
                    "rain_sum": [0.0, 4.5, 0.2],
                    "showers_sum": [0.0, 0.0, 0.0],
                    "snowfall_sum": [0.0, 0.0, 0.0],
                }
            }

    client = StubVenueClient(circuits_client=None)

    forecast = client.weather_forecast(43.74, 7.4199996, date(2026, 6, 5), date(2026, 6, 7))

    assert requested["url"] == "https://api.open-meteo.com/v1/forecast"
    assert requested["params"] == {
        "latitude": 43.74,
        "longitude": 7.4199996,
        "daily": (
            "weather_code,temperature_2m_max,temperature_2m_min,"
            "precipitation_probability_max,precipitation_sum,rain_sum,showers_sum,snowfall_sum"
        ),
        "timezone": "UTC",
        "start_date": "2026-06-05",
        "end_date": "2026-06-07",
    }
    assert [day["date"] for day in forecast] == ["2026-06-05", "2026-06-06", "2026-06-07"]
    assert forecast[1]["is_wet"] is True
    assert forecast[1]["summary"] == "Wet"
