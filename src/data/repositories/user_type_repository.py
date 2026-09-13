"""User type repository"""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.data.models.user_type_model import UserTypeModel
from src.data.repositories.base.base_repository import BaseRepository

class UserTypeRepository(BaseRepository[UserTypeModel]):
    """Repository for User Type entity (reference table)"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, UserTypeModel)
    
    async def get_by_description(self, description: str) -> Optional[UserTypeModel]:
        """Get user type by description"""
        stmt = select(UserTypeModel).where(UserTypeModel.description == description)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_with_permission(self, permission_field: str) -> list[UserTypeModel]:
        """Get all user types that have a specific permission"""
        if not hasattr(UserTypeModel, permission_field):
            return []
        
        stmt = select(UserTypeModel).where(getattr(UserTypeModel, permission_field) == True)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())