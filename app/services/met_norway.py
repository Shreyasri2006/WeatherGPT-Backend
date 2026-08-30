from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from typing import Any

import httpx

from app.config import get_settings
from app.models.schemas import CurrentWeather, DailyForecast, SourceInfo


MET_URL = "https://api.met.no/weatherapi/locationforecast/2.0/compact"


def _symbol_to_wmo(symbol: str | None) -> int | None:
    if not symbol:
        return None
    value = symbol.lower()
    if "thunder" in value:
        return 95
    if "snow" in value or "sleet" in value:
        return 71
    if "heavyrain" in value:
        return 65
    if "rain" in value:
        return 61
    if "fog" in value:
        return 45
    if "partlycloudy" in value:
        return 2
    if "cloudy" in value:
        return 3
    if "fair" in value:
        return 1
    if "clearsky" in value:
        return 0
    return None


class MetNorwayService:
    """Secondary no-key forecast provider used only when the primary feed is unavailable."""

    def __init__(self) -> None:
        self.settings = get_settings()

    async def forecast(
        self,
        latitude: float,
        longitude: float,
        days: int = 7,
    ) -> tuple[CurrentWeather, list[DailyForecast], SourceInfo]:
        headers = {
            "User-Agent": "WeatherGPT-SIH26068/0.1 https://github.com/Shreyasri2006/WeatherGPT-Backend",
        }
        params = {
            "lat": round(latitude, 4),
            "lon": round(longitude, 4),
        }
        async with httpx.AsyncClient(timeout=self.settings.http_timeout_seconds, headers=headers) as client:
            response = await client.get(MET_URL, params=params)
            response.raise_for_status()
            data = response.json()

        timeseries = data.get("properties", {}).get("timeseries", [])
        if not timeseries:
            raise RuntimeError("MET Norway returned no forecast data")

        first = timeseries[0]
        first_details = first.get("data", {}).get("instant", {}).get("details", {})
        first_next = first.get("data", {}).get("next_1_hours") or first.get("data", {}).get("next_6_hours") or {}
        first_summary = first_next.get("summary", {})
        first_precip = first_next.get("details", {}).get("precipitation_amount")

        current = CurrentWeather(
            temperature_c=first_details.get("air_temperature"),
            apparent_temperature_c=first_details.get("air_temperature"),
            humidity_pct=first_details.get("relative_humidity"),
            precipitation_mm=first_precip,
            rain_mm=first_precip,
            weather_code=_symbol_to_wmo(first_summary.get("symbol_code")),
            wind_speed_kmh=(first_details.get("wind_speed") * 3.6) if isinstance(first_details.get("wind_speed"), (int, float)) else None,
            wind_gust_kmh=(first_details.get("wind_speed_of_gust") * 3.6) if isinstance(first_details.get("wind_speed_of_gust"), (int, float)) else None,
            wind_direction_deg=first_details.get("wind_from_direction"),
            is_day=None,
            observed_at=first.get("time"),
        )

        by_day: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for item in timeseries:
            time_value = item.get("time")
            if not time_value:
                continue
            by_day[time_value[:10]].append(item)

        forecast: list[DailyForecast] = []
        for date, rows in list(by_day.items())[: min(max(days, 1), 9)]:
            temps: list[float] = []
            winds: list[float] = []
            gusts: list[float] = []
            precip_total = 0.0
            symbols: list[str] = []

            for row in rows:
                row_data = row.get("data", {})
                details = row_data.get("instant", {}).get("details", {})
                temp = details.get("air_temperature")
                wind = details.get("wind_speed")
                gust = details.get("wind_speed_of_gust")
                if isinstance(temp, (int, float)):
                    temps.append(float(temp))
                if isinstance(wind, (int, float)):
                    winds.append(float(wind) * 3.6)
                if isinstance(gust, (int, float)):
                    gusts.append(float(gust) * 3.6)

                period = row_data.get("next_1_hours") or row_data.get("next_6_hours") or {}
                amount = period.get("details", {}).get("precipitation_amount")
                if isinstance(amount, (int, float)):
                    precip_total += float(amount)
                symbol = period.get("summary", {}).get("symbol_code")
                if symbol:
                    symbols.append(symbol)

            representative_symbol = symbols[len(symbols) // 2] if symbols else None
            forecast.append(
                DailyForecast(
                    date=date,
                    weather_code=_symbol_to_wmo(representative_symbol),
                    temperature_max_c=round(max(temps), 1) if temps else None,
                    temperature_min_c=round(min(temps), 1) if temps else None,
                    precipitation_probability_max_pct=None,
                    precipitation_sum_mm=round(precip_total, 1),
                    wind_speed_max_kmh=round(max(winds), 1) if winds else None,
                    wind_gust_max_kmh=round(max(gusts), 1) if gusts else None,
                    uv_index_max=None,
                )
            )

        source = SourceInfo(
            name="MET Norway Locationforecast",
            type="forecast_api_fallback",
            official=False,
            fetched_at=datetime.now(timezone.utc).isoformat(),
            url="https://api.met.no/weatherapi/locationforecast/2.0/",
            note="Fallback live forecast used only when the primary Open-Meteo feed is unavailable or rate-limited.",
        )
        return current, forecast, source
