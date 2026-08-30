from __future__ import annotations

import httpx

from app.config import get_settings
from app.models.schemas import Location


NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"


class NominatimGeocodingService:
    def __init__(self) -> None:
        self.settings = get_settings()

    async def search_locations(self, query: str, count: int = 7) -> list[Location]:
        headers = {
            "User-Agent": "WeatherGPT-SIH26068/0.1 https://github.com/Shreyasri2006/WeatherGPT-Backend",
        }
        params = {
            "q": query,
            "format": "jsonv2",
            "limit": min(max(count, 1), 10),
            "addressdetails": 1,
        }
        async with httpx.AsyncClient(timeout=self.settings.http_timeout_seconds, headers=headers) as client:
            response = await client.get(NOMINATIM_URL, params=params)
            response.raise_for_status()
            data = response.json()

        results: list[Location] = []
        for row in data[:count]:
            address = row.get("address", {})
            name = (
                row.get("name")
                or address.get("city")
                or address.get("town")
                or address.get("village")
                or query
            )
            results.append(
                Location(
                    name=name,
                    latitude=float(row["lat"]),
                    longitude=float(row["lon"]),
                    country=address.get("country"),
                    admin1=address.get("state") or address.get("region"),
                )
            )
        return results
