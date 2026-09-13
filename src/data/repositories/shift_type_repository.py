"""Shift type repository"""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.data.models.shift_type_model import ShiftTypeModel
from src.data.repositories.base.base_repository import BaseRepository

class ShiftTypeRepository(BaseRepository):
    """Repository for Shift Type reference entity"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, ShiftTypeModel)
    
    async def get_by_description(self, description: str) -> Optional[ShiftTypeModel]:
        """Get shift type by description"""
        stmt = select(ShiftTypeModel).where(ShiftTypeModel.description == description)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()