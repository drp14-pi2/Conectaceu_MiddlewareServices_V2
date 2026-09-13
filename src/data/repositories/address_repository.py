"""Address repository"""
from typing import Optional, List
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import select

from src.data.models.address_model import AddressModel
from src.data.repositories.base.base_repository import BaseRepository

class AddressRepository(BaseRepository[AddressModel]):
    """Repository for Address entity"""
    
    def __init__(self, session: Session):
        super().__init__(session, AddressModel)
    
    async def get_by_user_id(self, user_id: UUID) -> List[AddressModel]:
        """Get all addresses for a user"""
        stmt = select(AddressModel).where(AddressModel.user_id == user_id)
        result = self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def get_primary_address(self, user_id: UUID) -> Optional[AddressModel]:
        """Get user's primary address (first one)"""
        addresses = await self.get_by_user_id(user_id)
        return addresses[0] if addresses else None
    
    async def get_by_zip_code(self, zip_code: str, skip: int = 0, limit: int = 100) -> List[AddressModel]:
        """Get addresses by ZIP code"""
        stmt = select(AddressModel).where(AddressModel.zip_code == zip_code).offset(skip).limit(limit)
        result = self.session.execute(stmt)
        return list(result.scalars().all())
