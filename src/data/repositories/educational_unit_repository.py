"""Educational unit repository"""
from typing import Optional, List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from src.data.models.educational_unit_model import EducationalUnitModel
from src.data.repositories.base.base_repository import BaseRepository

class EducationalUnitRepository(BaseRepository[EducationalUnitModel]):
    """Repository for educational unit model"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, EducationalUnitModel)

    async def get_by_name_and_address(
        self,
        name: str,
        zip_code: str,
        number: str
    ) -> bool:
        stmt = select(EducationalUnitModel).where(
            and_(
                EducationalUnitModel.name == name,
                EducationalUnitModel.zip_code == zip_code,
                EducationalUnitModel.number == number
            )
        )
        result = await self.session.execute(stmt)

        return result.scalar_one_or_none()

    async def get_by_id(self, id: UUID) -> Optional[EducationalUnitModel]:
        stmt = select(EducationalUnitModel).where(EducationalUnitModel.id == id)
        result = await self.session.execute(stmt)
        
        return result.scalar_one_or_none()
    
    async def list(self, active: Optional[bool] = None) -> List[EducationalUnitModel]:
        """Get all addresses for a user"""
        conditions = []

        if active is not None:
            conditions = [EducationalUnitModel.active == active]

        stmt = select(EducationalUnitModel)

        if conditions:
            stmt = stmt.where(conditions)

        result = await self.session.execute(stmt)
        
        return list(result.scalars().all())
    
    async def deactivate(self, id: UUID) -> bool:
        """Deactivate course"""
        unit = await self.get_by_id(id)

        if unit:
            unit.active = False
            await self.session.flush()

            return True
        
        return False
    
    async def activate(self, id: UUID) -> bool:
        """Activate course"""
        unit = await self.get_by_id(id)

        if unit:
            unit.active = True
            await self.session.flush()

            return True
        
        return False
