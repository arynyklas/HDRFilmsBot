import asyncio
import typing

from src.cache import AsyncTimedCache


CLEANUP_EXPIRED_CACHE_INTERVAL = 1.


async def cleanup_expired_cache_worker(*caches: AsyncTimedCache[typing.Any, typing.Any]) -> None:
    while True:
        for cache in caches:
            await cache.clean_expired()

        await asyncio.sleep(CLEANUP_EXPIRED_CACHE_INTERVAL)
