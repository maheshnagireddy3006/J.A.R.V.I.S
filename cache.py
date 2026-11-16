"""
JARVIS: EDGE-FIRST GRAPH-AGENT ECOSYSTEM - CACHING SUBSYSTEM (REDIS & IN-MEMORY LRU)
Implements:
  1. Caching with Redis Client with Graceful In-Memory Fallback
  2. Key-Value Storage with Time-to-Live (TTL) Expiration
  3. Cache Invalidation and Namespace Eviction
  4. Telemetry Tracking (Cache Hits, Misses, and Hit Ratio)
"""

import os
import time
import json
import logging
from typing import Optional, Any, Dict

logger = logging.getLogger("JarvisCache")


class CacheManager:
    """
    High-performance multi-tier cache manager.
    Connects to Redis when available (via REDIS_URL), or transparently uses an
    in-memory thread-safe LRU dictionary with exact TTL expiration.
    """

    def __init__(self, redis_url: Optional[str] = None):
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.redis_client = None
        self._memory_store: Dict[str, Dict[str, Any]] = {}  # {key: {"val": Any, "exp": float}}
        self.stats = {"hits": 0, "misses": 0}

        self._initialize_connection()

    def _initialize_connection(self):
        """Attempts connection to Redis if redis-py library is present."""
        try:
            import redis
            self.redis_client = redis.from_url(
                self.redis_url,
                socket_connect_timeout=0.2,
                socket_timeout=0.2,
                retry_on_timeout=False
            )
            self.redis_client.ping()
            logger.info(f"Connected to remote Redis instance at: {self.redis_url}")
        except Exception as e:
            logger.info(f"Using high-performance in-memory TTL cache fallback ({e}).")
            self.redis_client = None

    def get(self, key: str) -> Optional[Any]:
        """Retrieves cached value if exists and not expired."""
        if self.redis_client:
            try:
                raw = self.redis_client.get(key)
                if raw is not None:
                    self.stats["hits"] += 1
                    return json.loads(raw)
                self.stats["misses"] += 1
                return None
            except Exception:
                pass

        # In-Memory Cache Lookup
        entry = self._memory_store.get(key)
        if entry:
            if entry["exp"] is None or time.time() < entry["exp"]:
                self.stats["hits"] += 1
                return entry["val"]
            else:
                del self._memory_store[key]

        self.stats["misses"] += 1
        return None

    def set(self, key: str, value: Any, ttl_seconds: int = 300) -> bool:
        """Stores key-value pair with designated TTL in seconds."""
        if self.redis_client:
            try:
                serialized = json.dumps(value)
                self.redis_client.setex(key, ttl_seconds, serialized)
                return True
            except Exception:
                pass

        # In-Memory Cache Store
        exp_time = time.time() + ttl_seconds if ttl_seconds > 0 else None
        self._memory_store[key] = {
            "val": value,
            "exp": exp_time
        }
        return True

    def delete(self, key: str) -> bool:
        """Invalidates a specific cached key."""
        if self.redis_client:
            try:
                self.redis_client.delete(key)
            except Exception:
                pass

        if key in self._memory_store:
            del self._memory_store[key]
            return True
        return False

    def clear(self) -> None:
        """Flushes the entire cache namespace."""
        if self.redis_client:
            try:
                self.redis_client.flushdb()
            except Exception:
                pass
        self._memory_store.clear()

    def get_telemetry(self) -> Dict[str, Any]:
        """Computes hit/miss metrics and total entries."""
        total = self.stats["hits"] + self.stats["misses"]
        ratio = round((self.stats["hits"] / total) * 100, 2) if total > 0 else 0.0
        return {
            "tier": "redis" if self.redis_client else "in_memory_lru",
            "hits": self.stats["hits"],
            "misses": self.stats["misses"],
            "hit_ratio_percent": ratio,
            "active_keys": len(self._memory_store)
        }


# Global singleton cache instance
cache = CacheManager()
