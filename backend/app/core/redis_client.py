"""
Redis cache client singleton using aioredis.
"""
import json
from typing import Any, Optional
import redis.asyncio as aioredis
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

_redis_client: Optional[aioredis.Redis] = None


async def get_redis() -> aioredis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = await aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )
    return _redis_client


async def cache_get(key: str) -> Optional[Any]:
    try:
        r = await get_redis()
        val = await r.get(key)
        return json.loads(val) if val else None
    except Exception as e:
        logger.warning(f"Redis GET failed for {key}: {e}")
        return None


async def cache_set(key: str, value: Any, ttl: int = settings.CACHE_TTL_SECONDS) -> None:
    try:
        r = await get_redis()
        await r.setex(key, ttl, json.dumps(value, default=str))
    except Exception as e:
        logger.warning(f"Redis SET failed for {key}: {e}")


async def cache_delete(key: str) -> None:
    try:
        r = await get_redis()
        await r.delete(key)
    except Exception as e:
        logger.warning(f"Redis DELETE failed for {key}: {e}")


async def rate_limit_check(user_id: int, endpoint: str) -> bool:
    """
    Sliding window rate limiter.
    Returns True if request is allowed, False if rate-limited.
    """
    try:
        r = await get_redis()
        key = f"rate:{user_id}:{endpoint}"
        pipe = r.pipeline()
        pipe.incr(key)
        pipe.expire(key, settings.RATE_LIMIT_WINDOW_SECONDS)
        results = await pipe.execute()
        return results[0] <= settings.RATE_LIMIT_REQUESTS
    except Exception as e:
        logger.warning(f"Rate limit check failed: {e}")
        return True  # Fail open
