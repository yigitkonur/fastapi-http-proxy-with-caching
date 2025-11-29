"""
Pydantic models for request/response validation and serialization.
"""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class CachedResponse(BaseModel):
    """Represents a cached HTTP response."""
    
    status_code: int = Field(..., description="HTTP status code")
    headers: dict[str, str] = Field(default_factory=dict, description="Response headers")
    content: Any = Field(..., description="Response body content")
    content_type: str = Field(default="application/json", description="Content-Type of response")
    cached_at: datetime = Field(default_factory=datetime.utcnow, description="Cache timestamp")
    
    model_config = {"json_schema_extra": {"example": {
        "status_code": 200,
        "headers": {"x-custom": "header"},
        "content": {"message": "success"},
        "content_type": "application/json",
        "cached_at": "2024-01-01T12:00:00Z"
    }}}


class ProxyRequest(BaseModel):
    """Request model for proxy endpoint."""
    
    url: str = Field(..., description="Target URL to proxy the request to")
    method: str = Field(default="POST", description="HTTP method (GET, POST, PUT, DELETE, PATCH)")
    bypass_cache: bool = Field(default=False, description="Skip cache lookup and force fresh request")
    cache_ttl: Optional[int] = Field(default=None, description="Custom TTL for this request (overrides default)")
    
    model_config = {"json_schema_extra": {"example": {
        "url": "https://api.example.com/data",
        "method": "POST",
        "bypass_cache": False,
        "cache_ttl": 7200
    }}}


class ProxyResponse(BaseModel):
    """Response model for proxy endpoint."""
    
    success: bool = Field(..., description="Whether the request was successful")
    cached: bool = Field(..., description="Whether response came from cache")
    cache_key: str = Field(..., description="MD5 hash used as cache key")
    status_code: int = Field(..., description="HTTP status code from target")
    data: Any = Field(..., description="Response data from target")
    
    model_config = {"json_schema_extra": {"example": {
        "success": True,
        "cached": True,
        "cache_key": "a1b2c3d4e5f6789012345678",
        "status_code": 200,
        "data": {"message": "Hello from cached response"}
    }}}


class HealthResponse(BaseModel):
    """Health check response model."""
    
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="Application version")
    redis_connected: bool = Field(..., description="Redis connection status")
    cache_stats: Optional[dict[str, int]] = Field(None, description="Cache statistics")


class ErrorResponse(BaseModel):
    """Standard error response model."""
    
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[dict[str, Any]] = Field(None, description="Additional error details")
    
    model_config = {"json_schema_extra": {"example": {
        "error": "ProxyError",
        "message": "Failed to connect to target URL",
        "details": {"url": "https://api.example.com", "reason": "Connection timeout"}
    }}}


class CacheStatsResponse(BaseModel):
    """Cache statistics response model."""
    
    total_keys: int = Field(..., description="Total number of cached keys")
    memory_usage: Optional[str] = Field(None, description="Redis memory usage")
    prefix: str = Field(..., description="Cache key prefix in use")
