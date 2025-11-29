"""
FastAPI dependency injection providers.

Manages lifecycle of services and provides them to route handlers.
"""

from typing import AsyncGenerator

from app.config import Settings, get_settings
from app.services.cache import CacheService
from app.services.proxy import ProxyService

# Global service instances (initialized on startup)
_cache_service: CacheService | None = None
_proxy_service: ProxyService | None = None


async def init_services(settings: Settings) -> None:
    """
    Initialize all services on application startup.
    
    Called from the FastAPI lifespan context manager.
    Redis connection is optional - the proxy works without caching.
    """
    global _cache_service, _proxy_service
    
    # Initialize cache service (optional - continues if Redis unavailable)
    _cache_service = CacheService(settings)
    try:
        await _cache_service.connect()
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(
            f"Redis unavailable - running without cache: {e}"
        )
    
    # Initialize proxy service
    _proxy_service = ProxyService(settings)
    await _proxy_service.start()


async def shutdown_services() -> None:
    """
    Gracefully shutdown all services.
    
    Called from the FastAPI lifespan context manager.
    """
    global _cache_service, _proxy_service
    
    if _cache_service:
        await _cache_service.disconnect()
        _cache_service = None
    
    if _proxy_service:
        await _proxy_service.stop()
        _proxy_service = None


def get_cache_service() -> CacheService:
    """
    Dependency provider for CacheService.
    
    Returns:
        CacheService instance
        
    Raises:
        RuntimeError: If services not initialized
    """
    if _cache_service is None:
        raise RuntimeError("Cache service not initialized. Ensure app startup completed.")
    return _cache_service


def get_proxy_service() -> ProxyService:
    """
    Dependency provider for ProxyService.
    
    Returns:
        ProxyService instance
        
    Raises:
        RuntimeError: If services not initialized
    """
    if _proxy_service is None:
        raise RuntimeError("Proxy service not initialized. Ensure app startup completed.")
    return _proxy_service
