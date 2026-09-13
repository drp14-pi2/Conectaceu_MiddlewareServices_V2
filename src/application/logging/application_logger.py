"""Application-level logging"""
import traceback

from src.data.repositories.log_application_error_repository import LogApplicationErrorRepository
from src.data.db_context.database import AsyncSessionLocal


class ApplicationLogger:
    """Logger for application errors - can be used anywhere"""
    
    @staticmethod
    async def log_error(
        exception: Exception,
        reraise: bool = False
    ) -> None:
        """
        Log an exception to the database.
        Can be called from services, repositories, console apps, etc.
        
        Args:
            exception: The exception that occurred
            context: Optional additional context (e.g., "UserService.create_user")
        """
        
        async with AsyncSessionLocal() as session:
            try:
                repo = LogApplicationErrorRepository(session)
                stacktrace = traceback.format_exc()
                error_detail = str(exception)
                await repo.log(
                    exception=error_detail,
                    stacktrace=stacktrace
                )
                await session.commit()
            except Exception:
                pass  # Don't let logging failure break the app
            finally:
                await session.close()
                if reraise:
                    raise exception