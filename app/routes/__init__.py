"""
API routes module.

Contains all FastAPI route definitions organized by feature.
"""

from app.routes.proxy import router as proxy_router
from app.routes.health import router as health_router

__all__ = ["proxy_router", "health_router"]
