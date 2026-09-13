"""User gender type repository"""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.data.models.user_gender_type_model import UserGenderTypeModel
from src.data.repositories.base.base_repository import BaseRepository

class UserGenderTypeRepository(BaseRepository):
    """Repository for User Gender Type reference entity"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, UserGenderTypeModel)
    
    async def get_by_description(self, description: str) -> Optional[UserGenderTypeModel]:
        """Get gender type by description"""
        stmt = select(UserGenderTypeModel).where(UserGenderTypeModel.description == description)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()