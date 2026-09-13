"""Document request log repository - Insert only"""
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from src.data.models.log_document_request_model import LogDocumentRequestModel
from src.data.repositories.base.base_repository import BaseRepository

class LogDocumentRequestRepository(BaseRepository):
    """Repository for Document Request logs - Insert only"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, LogDocumentRequestModel)
    
    async def log(
        self,
        document_id: UUID,
        user_id: UUID,
        user_ip_address: str
    ) -> LogDocumentRequestModel:
        """Log a document request"""
        log = LogDocumentRequestModel(
            document_id=document_id,
            user_id=user_id,
            user_ip_address=user_ip_address
        )
        return await self.create(log)

    async def has_exceeded_requests(
        self,
        minutes: int,
        max_requests: int,
        user_id: UUID,
        origin_ip_address: Optional[str] = None,
    ) -> bool:
        """
        Returns True if the count of requests exceeds max_requests
        within the last `minutes` minutes.
        """
        cutoff = datetime.now() - timedelta(minutes=minutes)
        conditions = [
            LogDocumentRequestModel.user_id == user_id,
            LogDocumentRequestModel.created_at >= cutoff
        ]

        if origin_ip_address is not None:
            conditions.append(LogDocumentRequestModel.user_ip_address == origin_ip_address)

        stmt = select(func.count()).select_from(LogDocumentRequestModel).where(and_(*conditions))
        result = await self.session.execute(stmt)
        count = result.scalar() or 0

        return count >= max_requests
