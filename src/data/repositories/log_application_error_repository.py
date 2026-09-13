"""Application error log repository - Insert only"""
from sqlalchemy.ext.asyncio import AsyncSession
from src.data.models.log_application_error_model import LogApplicationErrorModel
from src.data.repositories.base.base_repository import BaseRepository

class LogApplicationErrorRepository(BaseRepository):
    """Repository for Application Error logs - Insert only"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, LogApplicationErrorModel)
    
    async def log(self, exception: str, stacktrace: str) -> LogApplicationErrorModel:
        """Log an application error"""
        error_log = LogApplicationErrorModel(
            exception=exception,
            stacktrace=stacktrace
        )
        return await self.create(error_log)