"""
Cache service for managing Redis-based response caching.

Uses MD5 hashing to generate deterministic cache keys from request signatures.
This approach ensures identical requests (same URL, headers, body) return
cached responses, which is perfect for no-code automation platforms.
"""

import hashlib
import json
import logging
from datetime import datetime
from typing import Any, Optional

import redis.asyncio as aioredis
from redis.exceptions import RedisError

from app.config import Settings
from app.models import CachedResponse

logger = logging.getLogger(__name__)


class CacheService:
    """
    Service for caching HTTP responses in Redis.
    
    Cache keys are MD5 hashes of the request signature (URL + sorted headers + body),
    ensuring that identical requests hit the same cache entry.
    
    Example usage:
        cache = CacheService(settings)
        await cache.connect()
        
        key = cache.generate_cache_key(url, headers, body)
        cached = await cache.get(key)
        if not cached:
            # fetch response...
            await cache.set(key, response)
    """
    
    def __init__(self, settings: Settings):
        """Initialize cache service with settings."""
        self._settings = settings
        self._client: Optional[aioredis.Redis] = None
        self._connected = False
    
    async def connect(self) -> None:
        """
        Establish connection to Redis.
        
        Raises:
            RedisError: If connection fails
        """
        try:
            self._client = aioredis.from_url(
                self._settings.redis_url,
                decode_responses=True,
                socket_connect_timeout=5.0,
            )
            # Test connection
            await self._client.ping()
            self._connected = True
            logger.info("Successfully connected to Redis")
        except RedisError as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self._connected = False
            raise
    
    async def disconnect(self) -> None:
        """Close Redis connection gracefully."""
        if self._client:
            await self._client.close()
            self._connected = False
            logger.info("Disconnected from Redis")
    
    @property
    def is_connected(self) -> bool:
        """Check if Redis connection is active."""
        return self._connected
    
    def generate_cache_key(
        self,
        url: str,
        headers: dict[str, str],
        body: bytes,
        method: str = "POST"
    ) -> str:
        """
        Generate MD5 cache key from request signature.
        
        The cache key is derived from:
        - HTTP method
        - Target URL
        - Sorted headers (excluding volatile headers)
        - Request body
        
        Args:
            url: Target URL
            headers: Request headers
            body: Request body as bytes
            method: HTTP method
            
        Returns:
            MD5 hash string prefixed with cache prefix
        """
        # Filter out volatile headers that shouldn't affect caching
        volatile_headers = {
            "x-request-id", "x-correlation-id", "date", "authorization",
            "x-forwarded-for", "x-real-ip", "cf-ray", "cf-connecting-ip"
        }
        filtered_headers = {
            k.lower(): v for k, v in headers.items()
            if k.lower() not in volatile_headers
        }
        
        # Build deterministic signature
        signature = {
            "method": method.upper(),
            "url": url,
            "headers": dict(sorted(filtered_headers.items())),
            "body_md5": hashlib.md5(body).hexdigest() if body else "",
        }
        
        # Generate MD5 hash of signature
        signature_json = json.dumps(signature, sort_keys=True, separators=(",", ":"))
        cache_hash = hashlib.md5(signature_json.encode("utf-8")).hexdigest()
        
        return f"{self._settings.cache_prefix}{cache_hash}"
    
    async def get(self, key: str) -> Optional[CachedResponse]:
        """
        Retrieve cached response by key.
        
        Args:
            key: Cache key (MD5 hash)
            
        Returns:
            CachedResponse if found, None otherwise
        """
        if not self._client:
            logger.warning("Cache get called but Redis not connected")
            return None
        
        try:
            data = await self._client.get(key)
            if data:
                logger.debug(f"Cache HIT for key: {key[-12:]}")
                return CachedResponse.model_validate_json(data)
            logger.debug(f"Cache MISS for key: {key[-12:]}")
            return None
        except RedisError as e:
            logger.error(f"Redis error on get: {e}")
            return None
        except Exception as e:
            logger.error(f"Error deserializing cached response: {e}")
            return None
    
    async def set(
        self,
        key: str,
        response: CachedResponse,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Store response in cache.
        
        Args:
            key: Cache key (MD5 hash)
            response: Response to cache
            ttl: Optional TTL override (uses default from settings if None)
            
        Returns:
            True if cached successfully, False otherwise
        """
        if not self._client:
            logger.warning("Cache set called but Redis not connected")
            return False
        
        try:
            serialized = response.model_dump_json()
            effective_ttl = ttl if ttl is not None else self._settings.cache_ttl_seconds
            
            if effective_ttl > 0:
                await self._client.setex(key, effective_ttl, serialized)
            else:
                await self._client.set(key, serialized)
            
            logger.debug(f"Cached response with key: {key[-12:]} (TTL: {effective_ttl}s)")
            return True
        except RedisError as e:
            logger.error(f"Redis error on set: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """
        Delete a cached entry.
        
        Args:
            key: Cache key to delete
            
        Returns:
            True if deleted, False otherwise
        """
        if not self._client:
            return False
        
        try:
            result = await self._client.delete(key)
            return result > 0
        except RedisError as e:
            logger.error(f"Redis error on delete: {e}")
            return False
    
    async def clear_all(self) -> int:
        """
        Clear all cached entries with the configured prefix.
        
        Returns:
            Number of keys deleted
        """
        if not self._client:
            return 0
        
        try:
            pattern = f"{self._settings.cache_prefix}*"
            keys = []
            async for key in self._client.scan_iter(match=pattern, count=100):
                keys.append(key)
            
            if keys:
                deleted = await self._client.delete(*keys)
                logger.info(f"Cleared {deleted} cached entries")
                return deleted
            return 0
        except RedisError as e:
            logger.error(f"Redis error on clear_all: {e}")
            return 0
    
    async def get_stats(self) -> dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache stats
        """
        if not self._client:
            return {"error": "Not connected"}
        
        try:
            pattern = f"{self._settings.cache_prefix}*"
            key_count = 0
            async for _ in self._client.scan_iter(match=pattern, count=100):
                key_count += 1
            
            info = await self._client.info("memory")
            
            return {
                "total_keys": key_count,
                "memory_used": info.get("used_memory_human", "unknown"),
                "prefix": self._settings.cache_prefix,
            }
        except RedisError as e:
            logger.error(f"Redis error on get_stats: {e}")
            return {"error": str(e)}
