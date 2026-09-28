"""Health check controller"""
from fastapi import APIRouter, Request

from src.infrastructure.configuration.settings import settings
from src.infrastructure.handlers.datetime_handler import DateTimeHandler
from src.api.middleware.rate_limiter import limiter

router = APIRouter(tags=["Health"])

@router.get("/health", status_code=200)
@limiter.limit("20/minute")
async def health_check(request: Request):
    """Health check endpoint"""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "timestamp": DateTimeHandler.now()
    }
