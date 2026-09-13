from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from src.data.models.log_access_model import LogAccessModel
from src.data.repositories.base.base_repository import BaseRepository

class LogAccessRepository(BaseRepository):
    '''Repository for user access logs'''

    def __init__(self, session: AsyncSession):
        super().__init__(session, LogAccessModel)

    async def log(
        self,
        success: bool,
        message: str,
        origin_ip_address: str,
        user_agent: str,
        user_id: UUID
    ) -> LogAccessModel:
        '''Log user access'''
        access_log = LogAccessModel(
            success=success,
            message=message,
            origin_ip_address=origin_ip_address,
            user_agent=user_agent,
            user_id=user_id
        )

        return await self.create(access_log)

    async def has_exceeded_failed_attempts(
        self,
        minutes: int,
        max_attempts: int,
        user_id: Optional[UUID] = None,
        origin_ip_address: Optional[str] = None,
    ) -> bool:
        """
        Returns True if the count of failed attempts exceeds max_attempts
        within the last `minutes` minutes.
        """
        cutoff = datetime.now() - timedelta(minutes=minutes)
        conditions = [
            LogAccessModel.success == False,
            LogAccessModel.created_at >= cutoff,
        ]

        if user_id is not None:
            conditions.append(LogAccessModel.user_id == user_id)

        if origin_ip_address is not None:
            conditions.append(LogAccessModel.origin_ip_address == origin_ip_address)

        stmt = select(func.count()).select_from(LogAccessModel).where(and_(*conditions))
        result = await self.session.execute(stmt)
        count = result.scalar() or 0

        return count >= max_attempts
