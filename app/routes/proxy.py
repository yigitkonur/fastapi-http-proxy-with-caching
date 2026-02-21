"""
Proxy endpoint routes.

Main proxy-http-cache functionality for forwarding HTTP requests
with MD5-based caching.
"""

import logging
from typing import Annotated, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import JSONResponse

from app.config import Settings, get_settings
from app.dependencies import get_cache_service, get_proxy_service
from app.models import CachedResponse, ErrorResponse, ProxyResponse
from app.services.cache import CacheService
from app.services.proxy import ProxyError, ProxyService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Proxy"])


@router.api_route(
    "/proxy",
    methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    response_model=ProxyResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Bad Request"},
        502: {"model": ErrorResponse, "description": "Bad Gateway - Target unreachable"},
        504: {"model": ErrorResponse, "description": "Gateway Timeout"},
    },
    summary="HTTP Caching Proxy",
    description="""
Forward HTTP requests to any URL with automatic MD5-based caching.

**How it works:**
1. Generate MD5 hash from request signature (URL + headers + body)
2. Check Redis cache for existing response
3. If cached, return immediately (cache hit)
4. If not cached, forward request to target URL
5. Cache the response for future identical requests

**Perfect for:**
- No-code platforms (n8n, Make, Zapier) needing response caching
- Reducing duplicate API calls to expensive services
- Development environments requiring deterministic responses
"""
)
async def proxy_request(
    request: Request,
    url: Annotated[str, Query(description="Target URL to proxy the request to")],
    settings: Annotated[Settings, Depends(get_settings)],
    cache: Annotated[CacheService, Depends(get_cache_service)],
    proxy: Annotated[ProxyService, Depends(get_proxy_service)],
    bypass_cache: Annotated[bool, Query(description="Skip cache and force fresh request")] = False,
    cache_ttl: Annotated[Optional[int], Query(description="Custom cache TTL in seconds")] = None,
) -> ProxyResponse:
    """
    HTTP caching proxy endpoint with MD5-based caching.
    
    The cache key is an MD5 hash of:
    - HTTP method
    - Target URL  
    - Sorted request headers (excluding volatile headers)
    - MD5 of request body
    
    This ensures identical requests always return the same cached response.
    """
    if not url:
        raise HTTPException(
            status_code=400,
            detail={"error": "ValidationError", "message": "Missing 'url' query parameter"}
        )
    
    # Extract request components
    method = request.method
    headers = dict(request.headers)
    body = await request.body()
    
    logger.info(f"Proxy request: {method} {url} (bypass_cache={bypass_cache})")
    
    # Generate cache key
    cache_key = cache.generate_cache_key(url, headers, body, method)
    logger.debug(f"Generated cache key: {cache_key}")
    
    # Check cache (unless bypassed)
    if not bypass_cache and cache.is_connected:
        cached_response = await cache.get(cache_key)
        if cached_response:
            logger.info(f"Cache HIT for {url}")
            return ProxyResponse(
                success=True,
                cached=True,
                cache_key=cache_key.split(":")[-1],  # Return just the hash
                status_code=cached_response.status_code,
                data=cached_response.content,
            )
    
    logger.info(f"Cache MISS for {url}, forwarding request")
    
    # Forward request to target
    try:
        response = await proxy.forward_request(
            url=url,
            method=method,
            headers=headers,
            body=body,
        )
    except ProxyError as e:
        logger.error(f"Proxy error: {e.message}")
        return JSONResponse(
            status_code=e.status_code,
            content={
                "error": "ProxyError",
                "message": e.message,
                "details": e.details,
            }
        )
    
    # Cache the response (only successful responses by default)
    if cache.is_connected and response.status_code < 400:
        await cache.set(cache_key, response, ttl=cache_ttl)
        logger.info(f"Cached response for {url}")
    
    return ProxyResponse(
        success=response.status_code < 400,
        cached=False,
        cache_key=cache_key.split(":")[-1],
        status_code=response.status_code,
        data=response.content,
    )


# Legacy endpoint for backward compatibility with existing n8n workflows
@router.post(
    "/webhook-test/post-response",
    response_model=ProxyResponse,
    summary="Legacy Proxy Endpoint",
    description="Legacy endpoint maintained for backward compatibility. Use /proxy instead.",
    deprecated=True,
)
async def legacy_proxy_request(
    request: Request,
    url: Annotated[str, Query(description="Target URL to proxy the request to")],
    settings: Annotated[Settings, Depends(get_settings)],
    cache: Annotated[CacheService, Depends(get_cache_service)],
    proxy: Annotated[ProxyService, Depends(get_proxy_service)],
) -> ProxyResponse:
    """
    Legacy proxy endpoint for backward compatibility.
    
    This endpoint is deprecated. Please migrate to /proxy which supports
    all HTTP methods and additional features like cache bypass.
    """
    return await proxy_request(
        request=request,
        url=url,
        settings=settings,
        cache=cache,
        proxy=proxy,
        bypass_cache=False,
        cache_ttl=None,
    )
