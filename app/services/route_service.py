from __future__ import annotations

import asyncio

from app.models.schemas import RoutePointRisk, RouteRequest
from app.services.open_meteo import OpenMeteoService
from app.services.risk_engine import assess_risk, derive_alerts


def interpolate_route(request: RouteRequest) -> list[tuple[float, float, str]]:
    points = []
    for idx in range(request.samples):
        fraction = idx / (request.samples - 1)
        lat = request.origin_latitude + (request.destination_latitude - request.origin_latitude) * fraction
        lon = request.origin_longitude + (request.destination_longitude - request.origin_longitude) * fraction
        if idx == 0:
            name = request.origin_name
        elif idx == request.samples - 1:
            name = request.destination_name
        else:
            name = f"Route point {idx + 1}"
        points.append((lat, lon, name))
    return points


async def route_risk(request: RouteRequest) -> list[RoutePointRisk]:
    service = OpenMeteoService()

    async def one(lat: float, lon: float, name: str) -> RoutePointRisk:
        current, forecast, _ = await service.forecast(lat, lon, days=2)
        alerts = derive_alerts(current, forecast)
        risk = assess_risk(current, forecast, alerts)
        today = forecast[0] if forecast else None
        return RoutePointRisk(
            name=name,
            latitude=lat,
            longitude=lon,
            risk_score=risk.score,
            risk_level=risk.level,
            precipitation_probability_pct=today.precipitation_probability_max_pct if today else None,
            wind_speed_kmh=today.wind_speed_max_kmh if today else None,
        )

    return await asyncio.gather(*(one(lat, lon, name) for lat, lon, name in interpolate_route(request)))
