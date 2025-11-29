"""
Proxy service for forwarding HTTP requests to target URLs.

Handles the actual HTTP communication with target services,
including proper error handling, timeout management, and
response normalization.
"""

import logging
from typing import Any, Optional

import httpx
from httpx import HTTPError, TimeoutException

from app.config import Settings
from app.models import CachedResponse

logger = logging.getLogger(__name__)


class ProxyError(Exception):
    """Base exception for proxy-related errors."""
    
    def __init__(self, message: str, status_code: int = 502, details: Optional[dict] = None):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)


class ProxyService:
    """
    Service for proxying HTTP requests to target URLs.
    
    Manages HTTP client lifecycle, handles various HTTP methods,
    and normalizes responses for caching.
    
    Example usage:
        proxy = ProxyService(settings)
        async with proxy:
            response = await proxy.forward_request(
                url="https://api.example.com/data",
                method="POST",
                headers={"Content-Type": "application/json"},
                body=b'{"key": "value"}'
            )
    """
    
    def __init__(self, settings: Settings):
        """Initialize proxy service with settings."""
        self._settings = settings
        self._client: Optional[httpx.AsyncClient] = None
    
    async def __aenter__(self) -> "ProxyService":
        """Async context manager entry - creates HTTP client."""
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit - closes HTTP client."""
        await self.stop()
    
    async def start(self) -> None:
        """Initialize the HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self._settings.proxy_timeout_seconds),
                follow_redirects=True,
                limits=httpx.Limits(
                    max_keepalive_connections=20,
                    max_connections=100,
                ),
            )
            logger.info("HTTP client initialized")
    
    async def stop(self) -> None:
        """Close the HTTP client gracefully."""
        if self._client:
            await self._client.aclose()
            self._client = None
            logger.info("HTTP client closed")
    
    def _filter_headers(self, headers: dict[str, str]) -> dict[str, str]:
        """
        Filter out headers that shouldn't be forwarded.
        
        Args:
            headers: Original request headers
            
        Returns:
            Filtered headers safe for forwarding
        """
        excluded = set(self._settings.excluded_headers)
        return {
            k: v for k, v in headers.items()
            if k.lower() not in excluded
        }
    
    async def forward_request(
        self,
        url: str,
        method: str = "POST",
        headers: Optional[dict[str, str]] = None,
        body: Optional[bytes] = None,
    ) -> CachedResponse:
        """
        Forward an HTTP request to the target URL.
        
        Args:
            url: Target URL to forward the request to
            method: HTTP method (GET, POST, PUT, DELETE, PATCH)
            headers: Request headers to forward
            body: Request body as bytes
            
        Returns:
            CachedResponse with the target's response data
            
        Raises:
            ProxyError: If the request fails
        """
        if not self._client:
            await self.start()
        
        filtered_headers = self._filter_headers(headers or {})
        method = method.upper()
        
        logger.info(f"Forwarding {method} request to: {url}")
        
        try:
            response = await self._client.request(
                method=method,
                url=url,
                headers=filtered_headers,
                content=body if method in ("POST", "PUT", "PATCH") else None,
            )
            
            # Log response status
            logger.info(f"Received response: {response.status_code} from {url}")
            
            # Parse response content
            content = self._parse_response_content(response)
            content_type = response.headers.get("content-type", "application/json")
            
            # Extract relevant response headers
            response_headers = {
                k: v for k, v in response.headers.items()
                if k.lower() in ("x-request-id", "x-correlation-id", "x-ratelimit-remaining")
            }
            
            return CachedResponse(
                status_code=response.status_code,
                headers=response_headers,
                content=content,
                content_type=content_type,
            )
            
        except TimeoutException as e:
            logger.error(f"Timeout while forwarding to {url}: {e}")
            raise ProxyError(
                message="Request timed out",
                status_code=504,
                details={"url": url, "timeout": self._settings.proxy_timeout_seconds}
            )
        except httpx.ConnectError as e:
            logger.error(f"Connection error to {url}: {e}")
            raise ProxyError(
                message="Failed to connect to target",
                status_code=502,
                details={"url": url, "error": str(e)}
            )
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error from {url}: {e.response.status_code}")
            # Still return the error response for caching
            content = self._parse_response_content(e.response)
            return CachedResponse(
                status_code=e.response.status_code,
                headers={},
                content=content,
                content_type=e.response.headers.get("content-type", "application/json"),
            )
        except HTTPError as e:
            logger.error(f"HTTP error while forwarding to {url}: {e}")
            raise ProxyError(
                message="HTTP error occurred",
                status_code=502,
                details={"url": url, "error": str(e)}
            )
    
    def _parse_response_content(self, response: httpx.Response) -> Any:
        """
        Parse response content based on content type.
        
        Attempts to parse as JSON first, falls back to text.
        
        Args:
            response: httpx Response object
            
        Returns:
            Parsed content (dict/list for JSON, str for text)
        """
        content_type = response.headers.get("content-type", "")
        
        if "application/json" in content_type:
            try:
                return response.json()
            except Exception:
                logger.warning("Failed to parse JSON response, returning as text")
                return response.text
        
        if "text/" in content_type:
            return response.text
        
        # For binary content, return base64 encoded string
        if response.content:
            import base64
            return {
                "_binary": True,
                "_encoding": "base64",
                "data": base64.b64encode(response.content).decode("ascii")
            }
        
        return None
