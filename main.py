"""
FastAPI Transparent HTTP Proxy with MD5-based Caching

Root entry point - imports the application from the app package.
Run with: uvicorn main:app --reload

For configuration, see .env.example and set environment variables.
"""

# Re-export the FastAPI app from the app package
from app.main import app

# This allows running with: python main.py
if __name__ == "__main__":
    import uvicorn
    from app.config import get_settings
    
    settings = get_settings()
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )
