"""Main FastAPI application entry point"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import sys
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent))

from src.api.middleware.error_logging_middleware import ErrorLoggingMiddleware
from src.infrastructure.configuration.settings import settings
from src.data.db_context.database import engine
from src.api.middleware.exception_handler import register_exception_handlers
from src.api.middleware.request_size_limit_middleware import RequestSizeLimitMiddleware

# Import all routers
from src.api.controllers.auth_controller import router as auth_router
from src.api.controllers.broadcast_controller import router as broadcast_router
from src.api.controllers.user_controller import router as user_router
from src.api.controllers.address_controller import router as address_router
from src.api.controllers.course_controller import router as course_router
from src.api.controllers.component_controller import router as component_router
from src.api.controllers.class_controller import router as class_router
from src.api.controllers.attendance_controller import router as attendance_router
from src.api.controllers.enrollment_controller import router as enrollment_router
from src.api.controllers.document_controller import router as document_router
from src.api.controllers.representative_controller import router as representative_router
from src.api.controllers.password_reset_controller import router as password_router
from src.api.controllers.reference_controller import router as reference_router
from src.api.controllers.report_controller import router as report_router
from src.api.controllers.health_controller import router as health_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events"""
    # Startup
    print(f"🚀 Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    print(f"📌 Environment: {settings.ENVIRONMENT}")
    print(f"🗄️ Database: {settings.DATABASE_NAME} on {settings.DATABASE_HOST}")
    
    # Initialize database connection pool
    try:
        # Test database connection
        with engine.connect() as conn:
            from sqlalchemy import text
            result = conn.execute(text("SELECT 1"))
            print(f"✅ Database connection successful")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        raise
    
    yield
    
    # Shutdown
    print("👋 Shutting down...")
    
    # Dispose of database engine
    engine.dispose()
    print("🗄️ Database connections closed")


def create_app() -> FastAPI:
    """Application factory pattern"""
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="ConectaCEU API",
        lifespan=lifespan,
        docs_url="/api/docs",
        redoc_url=None,
        openapi_url="/api/openapi.json"
    )
    
    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Register error logging middleware
    app.add_middleware(ErrorLoggingMiddleware)
    app.add_middleware(RequestSizeLimitMiddleware, max_size_mb=settings.MAX_REQUEST_SIZE_MB)
    
    # Register exception handlers
    register_exception_handlers(app)
    
    # Register API routes
    app.include_router(address_router, prefix="/api")
    app.include_router(attendance_router, prefix="/api")
    app.include_router(auth_router, prefix="/api")
    app.include_router(broadcast_router, prefix="/api")
    app.include_router(class_router, prefix="/api")
    app.include_router(component_router, prefix="/api")
    app.include_router(course_router, prefix="/api")
    app.include_router(document_router, prefix="/api")
    app.include_router(enrollment_router, prefix="/api")
    app.include_router(health_router, prefix="/api")
    app.include_router(password_router, prefix="/api")
    app.include_router(reference_router, prefix="/api")
    app.include_router(report_router, prefix="/api")
    app.include_router(representative_router, prefix="/api")
    app.include_router(user_router, prefix="/api")
    
    return app


# Create app instance
app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )