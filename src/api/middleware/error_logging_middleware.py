"""API-level error logging middleware"""
import traceback
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from src.data.repositories.log_application_error_repository import LogApplicationErrorRepository
from src.data.db_context.database import AsyncSessionLocal


class ErrorLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware that logs HTTP request errors to the database.
    Called automatically on every API request that fails.
    """
    
    async def dispatch(self, request: Request, call_next) -> Response:
        try:
            response = await call_next(request)
            return response
        except Exception as exc:
            await self._log_http_error(request, exc)
            raise  # Re-raise for exception handlers
    
    async def _log_http_error(self, request: Request, exception: Exception) -> None:
        """Log HTTP request error with full context"""
        async with AsyncSessionLocal() as session:
            try:
                repo = LogApplicationErrorRepository(session)
                
                # Build HTTP context
                http_context = (
                    f"HTTP Error\n"
                    f"Method: {request.method}\n"
                    f"Path: {request.url.path}\n"
                    f"Query: {request.url.query}\n"
                    f"Client: {request.client.host if request.client else 'unknown'}\n"
                    f"User-Agent: {request.headers.get('user-agent', 'unknown')}\n"
                    f"Error: {str(exception)}"
                )
                
                stacktrace = traceback.format_exc()
                
                await repo.log_error(
                    exception=http_context,
                    stacktrace=stacktrace
                )
                await session.commit()
            except Exception:
                pass
            finally:
                await session.close()