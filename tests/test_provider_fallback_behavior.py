import asyncio

import httpx

from app.models.schemas import CurrentWeather, DailyForecast, SourceInfo
from app.services import bundle as bundle_module


def test_bundle_uses_secondary_provider_when_primary_is_rate_limited(monkeypatch):
    class FailingPrimary:
        async def forecast(self, *args, **kwargs):
            request = httpx.Request("GET", "https://api.open-meteo.com/v1/forecast")
            response = httpx.Response(429, request=request)
            raise httpx.HTTPStatusError("rate limited", request=request, response=response)

        async def model_snapshots(self, *args, **kwargs):
            return []

    class WorkingFallback:
        async def forecast(self, *args, **kwargs):
            current = CurrentWeather(temperature_c=25)
            daily = [DailyForecast(date="2026-08-30", temperature_max_c=28, temperature_min_c=20)]
            source = SourceInfo(
                name="Fallback",
                type="forecast_api_fallback",
                official=False,
                fetched_at="2026-08-30T00:00:00+00:00",
            )
            return current, daily, source

    async def no_warnings(self, *args, **kwargs):
        return []

    monkeypatch.setattr(bundle_module, "OpenMeteoService", FailingPrimary)
    monkeypatch.setattr(bundle_module, "MetNorwayService", WorkingFallback)
    monkeypatch.setattr(bundle_module.IMDWarningService, "get_warnings", no_warnings)

    result = asyncio.run(bundle_module.build_weather_bundle(12.3, 76.6, "Mysuru", 7))
    assert result.current.temperature_c == 25
    assert result.sources[0].type == "forecast_api_fallback"
