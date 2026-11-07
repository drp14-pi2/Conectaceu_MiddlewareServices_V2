"""User gender type repository"""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.data.models.user_gender_type_model import ClassAttendanceTypeModel
from src.data.repositories.base.base_repository import BaseRepository

class ClassAttendanceTypeRepository(BaseRepository):
    """Repository for User Gender Type reference entity"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, ClassAttendanceTypeModel)
    
    async def get_by_description(self, description: str) -> Optional[ClassAttendanceTypeModel]:
        """Get gender type by description"""
        stmt = select(ClassAttendanceTypeModel).where(ClassAttendanceTypeModel.description == description)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
