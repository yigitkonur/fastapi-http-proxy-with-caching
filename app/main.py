"""
proxy-http-cache

A production-ready HTTP caching proxy designed for no-code platforms
and automation workflows. Caches responses based on MD5 hash of request
signatures to reduce duplicate API calls.

Key Features:
- MD5-based request deduplication
- Redis caching with configurable TTL
- Support for all HTTP methods
- Legacy endpoint compatibility
- Comprehensive health checks
- OpenAPI documentation
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app import __version__
from app.config import get_settings
from app.dependencies import init_services, shutdown_services
from app.routes import health_router, proxy_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan context manager.
    
    Handles startup and shutdown of services.
    """
    settings = get_settings()
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    
    # Startup
    await init_services(settings)
    logger.info("All services initialized successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down services...")
    await shutdown_services()
    logger.info("Shutdown complete")


def create_app() -> FastAPI:
    """
    Application factory for creating the FastAPI app.
    
    Returns:
        Configured FastAPI application instance
    """
    settings = get_settings()
    
    app = FastAPI(
        title=settings.app_name,
        description="""
## proxy-http-cache: HTTP Proxy with MD5-based Caching

A high-performance proxy service that caches HTTP responses based on
MD5 hashes of request signatures. Perfect for:

- **No-code platforms** (n8n, Make, Zapier) that need response caching
- **Cost reduction** by avoiding duplicate API calls to paid services  
- **Development** where deterministic responses are helpful

### How Caching Works

1. Each request generates an MD5 hash from: `method + URL + headers + body`
2. If a cached response exists for that hash, it's returned immediately
3. If not, the request is forwarded and the response is cached for future use

### Cache Key Generation

```
MD5(
  method: "POST",
  url: "https://api.example.com/endpoint",
  headers: { sorted headers },
  body_md5: "d41d8cd98f00b204e9800998ecf8427e"
)
```

This ensures identical requests always hit the same cache entry.
        """,
        version=settings.app_version,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Exception handlers
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "error": "InternalError",
                "message": "An unexpected error occurred",
            }
        )
    
    # Include routers
    app.include_router(proxy_router)
    app.include_router(health_router)
    
    return app


# Create application instance
app = create_app()


if __name__ == "__main__":
    import uvicorn
    
    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="debug" if settings.debug else "info",
    )
