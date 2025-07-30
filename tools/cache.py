import redis
import json
import os
from dotenv import load_dotenv
from typing import Optional

load_dotenv()

# Redis connection
REDIS_URL = os.getenv("REDIS_URL")
redis_client = None

if REDIS_URL:
    try:
        redis_client = redis.from_url(REDIS_URL, decode_responses=True)
        # Test connection
        redis_client.ping()
        print("✅ Redis connected successfully")
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        redis_client = None
else:
    print("⚠️ REDIS_URL not found in environment variables")

# TTL mapping (in seconds)
TTL_MAP = {
    "day": 8 * 3600,  # 8 hours
    "week": 48 * 3600,  # 2 days (48 hours)
    "month": 168 * 3600,  # 1 week (168 hours)
}


def get_cache_key(profession: str, time_period: str) -> str:
    """Generate cache key from profession and time period"""
    return f"newsletter_{profession.lower()}_{time_period}"


def get_cached_newsletter(profession: str, time_period: str) -> Optional[str]:
    """Get newsletter from cache if it exists and hasn't expired"""
    if not redis_client:
        return None

    try:
        cache_key = get_cache_key(profession, time_period)
        cached_newsletter = redis_client.get(cache_key)

        if cached_newsletter:
            print(f"✅ Cache HIT for {profession} ({time_period})")
            return cached_newsletter
        else:
            print(f"❌ Cache MISS for {profession} ({time_period})")
            return None

    except Exception as e:
        print(f"⚠️ Cache retrieval error: {e}")
        return None


def cache_newsletter(profession: str, time_period: str, newsletter: str) -> bool:
    """Cache newsletter with appropriate TTL based on time period"""
    if not redis_client:
        return False

    try:
        cache_key = get_cache_key(profession, time_period)
        ttl_seconds = TTL_MAP.get(time_period, TTL_MAP["day"])  # Default to day TTL

        # Store with expiration
        redis_client.setex(cache_key, ttl_seconds, newsletter)

        # Convert seconds to human readable for logging
        hours = ttl_seconds // 3600
        print(
            f"✅ Cached newsletter for {profession} ({time_period}) - expires in {hours} hours"
        )
        return True

    except Exception as e:
        print(f"⚠️ Cache storage error: {e}")
        return False


def clear_cache_for_profession(profession: str) -> int:
    """Clear all cached newsletters for a specific profession (useful for debugging)"""
    if not redis_client:
        return 0

    try:
        pattern = f"newsletter_{profession.lower()}_*"
        keys = redis_client.keys(pattern)
        if keys:
            deleted = redis_client.delete(*keys)
            print(f"🗑️ Cleared {deleted} cached newsletters for {profession}")
            return deleted
        return 0
    except Exception as e:
        print(f"⚠️ Cache clear error: {e}")
        return 0


def get_cache_stats() -> dict:
    """Get cache statistics (useful for monitoring)"""
    if not redis_client:
        return {"error": "Redis not connected"}

    try:
        info = redis_client.info()
        newsletter_keys = len(redis_client.keys("newsletter_*"))

        return {
            "connected": True,
            "newsletter_count": newsletter_keys,
            "memory_used": info.get("used_memory_human", "unknown"),
            "uptime": info.get("uptime_in_seconds", 0),
        }
    except Exception as e:
        return {"error": str(e)}
