from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import httpx

from app.config import get_settings
from app.models.schemas import WeatherAlert


class IMDWarningService:
    """
    Optional adapter for an IMD integration gateway.

    Why a gateway contract instead of hard-coding a single IMD endpoint?
    The SIH prototype may receive different IMD feeds/credentials. Normalize those
    feeds into the JSON contract documented in API.md, then point IMD_WARNING_URL
    here. Until configured, this service returns no official warnings and the UI
    clearly labels derived hazards as non-official.
    """

    def __init__(self) -> None:
        self.settings = get_settings()

    async def get_warnings(self, latitude: float, longitude: float) -> list[WeatherAlert]:
        if not self.settings.imd_warning_url:
            return []
        headers: dict[str, str] = {}
        if self.settings.imd_api_key:
            headers["Authorization"] = f"Bearer {self.settings.imd_api_key}"
        async with httpx.AsyncClient(timeout=self.settings.http_timeout_seconds) as client:
            response = await client.get(
                self.settings.imd_warning_url,
                params={"latitude": latitude, "longitude": longitude},
                headers=headers,
            )
            response.raise_for_status()
            payload: Any = response.json()

        rows = payload.get("alerts", payload if isinstance(payload, list) else [])
        alerts: list[WeatherAlert] = []
        for idx, item in enumerate(rows):
            if not isinstance(item, dict):
                continue
            alerts.append(
                WeatherAlert(
                    id=str(item.get("id", f"imd-{idx}")),
                    severity=str(item.get("severity", "high")).lower(),
                    hazard=str(item.get("hazard", "weather_warning")),
                    title=str(item.get("title", "IMD weather warning")),
                    message=str(item.get("message", item.get("description", "Official warning active."))),
                    official=True,
                    source=str(item.get("source", "India Meteorological Department")),
                    issued_at=str(item.get("issued_at", datetime.now(timezone.utc).isoformat())),
                    valid_until=item.get("valid_until"),
                    safety_actions=[str(x) for x in item.get("safety_actions", [])],
                )
            )
        return alerts
