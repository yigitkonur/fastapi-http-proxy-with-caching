"""
Health check and administrative endpoints.
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.config import Settings, get_settings
from app.models import CacheStatsResponse, HealthResponse
from app.dependencies import get_cache_service
from app.services.cache import CacheService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Health & Admin"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health Check",
    description="Check the health status of the proxy service and its dependencies."
)
async def health_check(
    settings: Annotated[Settings, Depends(get_settings)],
    cache: Annotated[CacheService, Depends(get_cache_service)],
) -> HealthResponse:
    """
    Health check endpoint for monitoring and load balancers.
    
    Returns service status, version, and Redis connection state.
    """
    stats = None
    if cache.is_connected:
        stats_data = await cache.get_stats()
        if "error" not in stats_data:
            stats = {"total_keys": stats_data.get("total_keys", 0)}
    
    return HealthResponse(
        status="healthy" if cache.is_connected else "degraded",
        version=settings.app_version,
        redis_connected=cache.is_connected,
        cache_stats=stats,
    )


@router.get(
    "/cache/stats",
    response_model=CacheStatsResponse,
    summary="Cache Statistics",
    description="Get detailed statistics about the cache."
)
async def cache_stats(
    cache: Annotated[CacheService, Depends(get_cache_service)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> CacheStatsResponse:
    """
    Get cache statistics including key count and memory usage.
    """
    if not cache.is_connected:
        raise HTTPException(status_code=503, detail="Cache service unavailable")
    
    stats = await cache.get_stats()
    
    return CacheStatsResponse(
        total_keys=stats.get("total_keys", 0),
        memory_usage=stats.get("memory_used"),
        prefix=settings.cache_prefix,
    )


@router.delete(
    "/cache",
    summary="Clear Cache",
    description="Clear all cached entries. Use with caution in production."
)
async def clear_cache(
    cache: Annotated[CacheService, Depends(get_cache_service)],
) -> dict:
    """
    Clear all cached proxy responses.
    
    Returns the number of entries deleted.
    """
    if not cache.is_connected:
        raise HTTPException(status_code=503, detail="Cache service unavailable")
    
    deleted = await cache.clear_all()
    logger.info(f"Cache cleared: {deleted} entries deleted")
    
    return {"deleted": deleted, "message": f"Cleared {deleted} cached entries"}
