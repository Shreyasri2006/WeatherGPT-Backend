from __future__ import annotations

from datetime import datetime, timezone

from app.models.schemas import Location, SourceInfo, WeatherBundle
from app.services.historical import climate_context
from app.services.imd import IMDWarningService
from app.services.model_agreement import calculate_agreement
from app.services.open_meteo import OpenMeteoService
from app.services.risk_engine import assess_risk, derive_alerts


async def build_weather_bundle(latitude: float, longitude: float, location_name: str = "Selected location", days: int = 7) -> WeatherBundle:
    open_meteo = OpenMeteoService()
    current, forecast, live_source = await open_meteo.forecast(latitude, longitude, days=days)
    models = await open_meteo.model_snapshots(latitude, longitude)
    agreement = calculate_agreement(models)

    derived_alerts = derive_alerts(current, forecast)
    official_alerts = await IMDWarningService().get_warnings(latitude, longitude)
    alerts = official_alerts + derived_alerts
    risk = assess_risk(current, forecast, alerts)

    target_month = None
    if forecast:
        try:
            target_month = datetime.fromisoformat(forecast[0].date).month
        except ValueError:
            pass
    climate = climate_context(
        city=location_name,
        current_max_temp=forecast[0].temperature_max_c if forecast else None,
        target_month=target_month,
    )

    fetched_at = datetime.now(timezone.utc).isoformat()
    sources = [live_source]
    for model in models:
        sources.append(
            SourceInfo(
                name=model.model,
                type="nwp_model",
                official=False,
                fetched_at=fetched_at,
                url="https://open-meteo.com/",
                note="Used for cross-model agreement in the prototype.",
            )
        )
    if official_alerts:
        sources.append(
            SourceInfo(
                name="India Meteorological Department warning adapter",
                type="official_warning",
                official=True,
                fetched_at=fetched_at,
                note="Configured through IMD_WARNING_URL; source payload normalized by the backend adapter.",
            )
        )

    return WeatherBundle(
        location=Location(name=location_name, latitude=latitude, longitude=longitude),
        current=current,
        forecast=forecast,
        alerts=alerts,
        agreement=agreement,
        risk=risk,
        sources=sources,
        climate=climate,
    )
