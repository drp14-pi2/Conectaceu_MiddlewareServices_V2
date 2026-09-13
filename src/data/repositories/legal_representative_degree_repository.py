"""Legal representative degree repository"""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.data.models.legal_representative_degree_model import LegalRepresentativeDegreeModel
from src.data.repositories.base.base_repository import BaseRepository

class LegalRepresentativeDegreeRepository(BaseRepository):
    """Repository for Legal Representative Degree reference entity"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, LegalRepresentativeDegreeModel)
    
    async def get_by_description(self, description: str) -> Optional[LegalRepresentativeDegreeModel]:
        """Get legal representative degree by description"""
        stmt = select(LegalRepresentativeDegreeModel).where(LegalRepresentativeDegreeModel.description == description)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()