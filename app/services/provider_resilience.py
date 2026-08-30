from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from typing import Any, Awaitable, Callable

import httpx


@dataclass
class CacheEntry:
    value: Any
    expires_at: float
    stale_until: float


class TTLCache:
    def __init__(self) -> None:
        self._items: dict[str, CacheEntry] = {}
        self._lock = asyncio.Lock()

    async def get_fresh(self, key: str) -> Any | None:
        now = time.monotonic()
        async with self._lock:
            entry = self._items.get(key)
            if not entry:
                return None
            if now <= entry.expires_at:
                return entry.value
            return None

    async def get_stale(self, key: str) -> Any | None:
        now = time.monotonic()
        async with self._lock:
            entry = self._items.get(key)
            if not entry:
                return None
            if now <= entry.stale_until:
                return entry.value
            self._items.pop(key, None)
            return None

    async def set(self, key: str, value: Any, ttl_seconds: int, stale_seconds: int) -> None:
        now = time.monotonic()
        async with self._lock:
            self._items[key] = CacheEntry(
                value=value,
                expires_at=now + ttl_seconds,
                stale_until=now + max(ttl_seconds, stale_seconds),
            )


async def request_json_with_retry(
    client: httpx.AsyncClient,
    url: str,
    params: dict[str, Any],
    *,
    attempts: int = 3,
) -> dict[str, Any]:
    last_error: Exception | None = None

    for attempt in range(attempts):
        try:
            response = await client.get(url, params=params)
            if response.status_code == 429:
                retry_after = response.headers.get("Retry-After")
                try:
                    delay = float(retry_after) if retry_after else 1.0 * (2**attempt)
                except ValueError:
                    delay = 1.0 * (2**attempt)
                last_error = httpx.HTTPStatusError(
                    "Weather provider rate limited the request",
                    request=response.request,
                    response=response,
                )
                if attempt < attempts - 1:
                    await asyncio.sleep(min(delay, 6.0))
                    continue
                raise last_error

            response.raise_for_status()
            return response.json()
        except (httpx.TimeoutException, httpx.NetworkError) as exc:
            last_error = exc
            if attempt < attempts - 1:
                await asyncio.sleep(0.75 * (2**attempt))
                continue
            raise

    if last_error:
        raise last_error
    raise RuntimeError("Weather provider request failed")
