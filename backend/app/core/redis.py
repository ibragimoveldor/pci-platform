"""
Redis client configuration for caching and pub/sub.
"""
from typing import Optional

import redis.asyncio as redis
from redis.asyncio import Redis

from app.config import settings


# =============================================================================
# Redis Connection Pool
# =============================================================================
_redis_pool: Optional[Redis] = None


async def get_redis() -> Redis:
    """
    Get Redis client instance.
    Uses connection pooling for efficiency.
    """
    global _redis_pool
    
    if _redis_pool is None:
        _redis_pool = redis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
            max_connections=20,
        )
    
    return _redis_pool


async def close_redis():
    """Close Redis connection pool."""
    global _redis_pool
    
    if _redis_pool is not None:
        await _redis_pool.close()
        _redis_pool = None


# =============================================================================
# Cache Utilities
# =============================================================================
class RedisCache:
    """Simple caching utilities using Redis."""
    
    def __init__(self, prefix: str = "pci"):
        self.prefix = prefix
    
    def _make_key(self, key: str) -> str:
        return f"{self.prefix}:{key}"
    
    async def get(self, key: str) -> Optional[str]:
        """Get cached value."""
        redis_client = await get_redis()
        return await redis_client.get(self._make_key(key))
    
    async def set(
        self,
        key: str,
        value: str,
        expire_seconds: int = 3600,
    ) -> bool:
        """Set cached value with expiration."""
        redis_client = await get_redis()
        return await redis_client.setex(
            self._make_key(key),
            expire_seconds,
            value,
        )
    
    async def delete(self, key: str) -> int:
        """Delete cached value."""
        redis_client = await get_redis()
        return await redis_client.delete(self._make_key(key))
    
    async def exists(self, key: str) -> bool:
        """Check if key exists."""
        redis_client = await get_redis()
        return await redis_client.exists(self._make_key(key)) > 0


# =============================================================================
# Task Status Tracking
# =============================================================================
class TaskStatusTracker:
    """
    Track background task status in Redis.
    Enables real-time progress updates via polling or WebSockets.
    """
    
    PREFIX = "task_status"
    
    @classmethod
    async def set_status(
        cls,
        task_id: str,
        status: str,
        progress: int = 0,
        message: str = "",
        result: Optional[dict] = None,
    ):
        """Update task status."""
        import json
        
        redis_client = await get_redis()
        data = {
            "status": status,
            "progress": progress,
            "message": message,
            "result": result,
        }
        await redis_client.setex(
            f"{cls.PREFIX}:{task_id}",
            3600 * 24,  # 24 hour expiry
            json.dumps(data),
        )
    
    @classmethod
    async def get_status(cls, task_id: str) -> Optional[dict]:
        """Get task status."""
        import json
        
        redis_client = await get_redis()
        data = await redis_client.get(f"{cls.PREFIX}:{task_id}")
        
        if data:
            return json.loads(data)
        return None


# Global cache instance
cache = RedisCache()
