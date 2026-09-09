"""Health check controller"""
from fastapi import APIRouter

from src.infrastructure.configuration.settings import settings
from src.infrastructure.handlers.datetime_handler import DateTimeHandler

router = APIRouter(tags=["Health"])

@router.get("/health", status_code=200)
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "timestamp": DateTimeHandler.now()
    }
