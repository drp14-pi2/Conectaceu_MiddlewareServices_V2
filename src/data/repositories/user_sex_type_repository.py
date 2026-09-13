"""User sex type repository"""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.data.models.user_sex_type_model import UserSexTypeModel
from src.data.repositories.base.base_repository import BaseRepository

class UserSexTypeRepository(BaseRepository):
    """Repository for User Sex Type reference entity"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, UserSexTypeModel)
    
    async def get_by_description(self, description: str) -> Optional[UserSexTypeModel]:
        """Get sex type by description"""
        stmt = select(UserSexTypeModel).where(UserSexTypeModel.description == description)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()