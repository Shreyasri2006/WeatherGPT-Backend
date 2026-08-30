from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any

import httpx

from app.config import get_settings
from app.models.schemas import CurrentWeather, DailyForecast, Location, ModelSnapshot, SourceInfo
from app.services.geocoding_fallback import NominatimGeocodingService
from app.services.provider_resilience import TTLCache, request_json_with_retry


FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
GFS_URL = "https://api.open-meteo.com/v1/gfs"
ECMWF_URL = "https://api.open-meteo.com/v1/ecmwf"
GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"

_CACHE = TTLCache()


class OpenMeteoService:
    def __init__(self) -> None:
        self.settings = get_settings()

    @staticmethod
    def _cache_key(url: str, params: dict[str, Any]) -> str:
        normalized: list[tuple[str, str]] = []
        for key, value in sorted(params.items()):
            if key in {"latitude", "longitude"} and isinstance(value, (int, float)):
                value = round(float(value), 4)
            normalized.append((key, str(value)))
        return f"{url}|{normalized!r}"

    async def _get(
        self,
        url: str,
        params: dict[str, Any],
        *,
        ttl_seconds: int,
        stale_seconds: int,
    ) -> dict[str, Any]:
        cache_key = self._cache_key(url, params)
        fresh = await _CACHE.get_fresh(cache_key)
        if fresh is not None:
            return fresh

        headers = {
            "User-Agent": "WeatherGPT-SIH26068/0.1 https://github.com/Shreyasri2006/WeatherGPT-Backend",
        }
        try:
            async with httpx.AsyncClient(
                timeout=self.settings.http_timeout_seconds,
                headers=headers,
            ) as client:
                data = await request_json_with_retry(client, url, params, attempts=3)
            await _CACHE.set(cache_key, data, ttl_seconds=ttl_seconds, stale_seconds=stale_seconds)
            return data
        except httpx.HTTPError:
            stale = await _CACHE.get_stale(cache_key)
            if stale is not None:
                return stale
            raise

    async def search_locations(self, query: str, count: int = 7) -> list[Location]:
        try:
            data = await self._get(
                GEOCODE_URL,
                {"name": query, "count": count, "language": "en", "format": "json"},
                ttl_seconds=3600,
                stale_seconds=86400,
            )
            results = []
            for row in data.get("results", [])[:count]:
                results.append(
                    Location(
                        name=row.get("name", query),
                        latitude=row["latitude"],
                        longitude=row["longitude"],
                        country=row.get("country"),
                        admin1=row.get("admin1"),
                    )
                )
            return results
        except httpx.HTTPError:
            return await NominatimGeocodingService().search_locations(query, count=count)

    async def forecast(self, latitude: float, longitude: float, days: int = 7) -> tuple[CurrentWeather, list[DailyForecast], SourceInfo]:
        params = {
            "latitude": round(latitude, 4),
            "longitude": round(longitude, 4),
            "timezone": "auto",
            "forecast_days": min(max(days, 1), 16),
            "current": ",".join(
                [
                    "temperature_2m",
                    "relative_humidity_2m",
                    "apparent_temperature",
                    "precipitation",
                    "rain",
                    "weather_code",
                    "wind_speed_10m",
                    "wind_direction_10m",
                    "wind_gusts_10m",
                    "is_day",
                ]
            ),
            "daily": ",".join(
                [
                    "weather_code",
                    "temperature_2m_max",
                    "temperature_2m_min",
                    "precipitation_probability_max",
                    "precipitation_sum",
                    "wind_speed_10m_max",
                    "wind_gusts_10m_max",
                    "uv_index_max",
                ]
            ),
        }
        data = await self._get(
            FORECAST_URL,
            params,
            ttl_seconds=300,
            stale_seconds=1800,
        )
        current_raw = data.get("current", {})
        current = CurrentWeather(
            temperature_c=current_raw.get("temperature_2m"),
            apparent_temperature_c=current_raw.get("apparent_temperature"),
            humidity_pct=current_raw.get("relative_humidity_2m"),
            precipitation_mm=current_raw.get("precipitation"),
            rain_mm=current_raw.get("rain"),
            weather_code=current_raw.get("weather_code"),
            wind_speed_kmh=current_raw.get("wind_speed_10m"),
            wind_gust_kmh=current_raw.get("wind_gusts_10m"),
            wind_direction_deg=current_raw.get("wind_direction_10m"),
            is_day=current_raw.get("is_day"),
            observed_at=current_raw.get("time"),
        )

        daily = data.get("daily", {})
        dates = daily.get("time", [])
        forecast: list[DailyForecast] = []
        for idx, date in enumerate(dates):
            def value(key: str):
                values = daily.get(key, [])
                return values[idx] if idx < len(values) else None

            forecast.append(
                DailyForecast(
                    date=date,
                    weather_code=value("weather_code"),
                    temperature_max_c=value("temperature_2m_max"),
                    temperature_min_c=value("temperature_2m_min"),
                    precipitation_probability_max_pct=value("precipitation_probability_max"),
                    precipitation_sum_mm=value("precipitation_sum"),
                    wind_speed_max_kmh=value("wind_speed_10m_max"),
                    wind_gust_max_kmh=value("wind_gusts_10m_max"),
                    uv_index_max=value("uv_index_max"),
                )
            )

        source = SourceInfo(
            name="Open-Meteo Best Match",
            type="forecast_api",
            official=False,
            fetched_at=datetime.now(timezone.utc).isoformat(),
            url="https://open-meteo.com/",
            note="Primary prototype live-data source with server-side caching and rate-limit protection.",
        )
        return current, forecast, source

    async def _model_snapshot(self, url: str, model_name: str, latitude: float, longitude: float) -> ModelSnapshot:
        params = {
            "latitude": round(latitude, 4),
            "longitude": round(longitude, 4),
            "timezone": "auto",
            "forecast_days": 2,
            "hourly": "temperature_2m,precipitation,wind_speed_10m",
        }
        data = await self._get(
            url,
            params,
            ttl_seconds=1200,
            stale_seconds=7200,
        )
        hourly = data.get("hourly", {})
        precip = [x for x in hourly.get("precipitation", [])[:24] if isinstance(x, (int, float))]
        temp = [x for x in hourly.get("temperature_2m", [])[:24] if isinstance(x, (int, float))]
        wind = [x for x in hourly.get("wind_speed_10m", [])[:24] if isinstance(x, (int, float))]
        return ModelSnapshot(
            model=model_name,
            precipitation_24h_mm=round(sum(precip), 1) if precip else None,
            max_temperature_24h_c=round(max(temp), 1) if temp else None,
            max_wind_24h_kmh=round(max(wind), 1) if wind else None,
        )

    async def model_snapshots(self, latitude: float, longitude: float) -> list[ModelSnapshot]:
        tasks = [
            self._model_snapshot(GFS_URL, "NOAA GFS", latitude, longitude),
            self._model_snapshot(ECMWF_URL, "ECMWF IFS", latitude, longitude),
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        snapshots: list[ModelSnapshot] = []
        for result in results:
            if isinstance(result, ModelSnapshot):
                snapshots.append(result)
        return snapshots
