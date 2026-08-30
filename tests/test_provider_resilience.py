import asyncio

from app.services.provider_resilience import TTLCache


def test_ttl_cache_returns_fresh_value():
    async def scenario():
        cache = TTLCache()
        await cache.set("weather", {"ok": True}, ttl_seconds=60, stale_seconds=120)
        assert await cache.get_fresh("weather") == {"ok": True}
        assert await cache.get_stale("weather") == {"ok": True}

    asyncio.run(scenario())


def test_ttl_cache_missing_key_returns_none():
    async def scenario():
        cache = TTLCache()
        assert await cache.get_fresh("missing") is None
        assert await cache.get_stale("missing") is None

    asyncio.run(scenario())
