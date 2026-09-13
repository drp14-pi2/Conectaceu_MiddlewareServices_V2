"""Report type repository"""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.data.models.report_type_model import ReportTypeModel
from src.data.repositories.base.base_repository import BaseRepository

class ReportTypeRepository(BaseRepository):
    """Repository for Report Type reference entity"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, ReportTypeModel)
    
    async def get_by_description(self, description: str) -> Optional[ReportTypeModel]:
        """Get report type by description"""
        stmt = select(ReportTypeModel).where(ReportTypeModel.description == description)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()