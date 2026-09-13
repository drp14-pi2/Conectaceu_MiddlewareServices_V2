"""Legal representative repository"""
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import select

from src.data.models.legal_representative_model import LegalRepresentativeModel
from src.data.repositories.base.base_repository import BaseRepository

class LegalRepresentativeRepository(BaseRepository):
    """Repository for Legal Representative entity"""
    
    def __init__(self, session: Session):
        super().__init__(session, LegalRepresentativeModel)
    
    async def get_by_user_id(self, user_id: UUID) -> List[LegalRepresentativeModel]:
        """Get all legal representatives for a user (minor)"""
        stmt = select(LegalRepresentativeModel).where(
            LegalRepresentativeModel.user_id == user_id
        )
        result = self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def get_by_document(self, document: str) -> Optional[LegalRepresentativeModel]:
        """Get legal representative by document (CPF)"""
        stmt = select(LegalRepresentativeModel).where(
            LegalRepresentativeModel.document == document
        )
        result = self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_primary_representative(self, user_id: UUID) -> Optional[LegalRepresentativeModel]:
        """Get the primary (first) legal representative for a user"""
        representatives = await self.get_by_user_id(user_id)
        return representatives[0] if representatives else None
    
    async def document_exists(self, document: str, exclude_id: Optional[UUID] = None) -> bool:
        """Check if document already exists"""
        stmt = select(LegalRepresentativeModel).where(
            LegalRepresentativeModel.document == document
        )
        
        if exclude_id:
            stmt = stmt.where(LegalRepresentativeModel.id != exclude_id)
        
        result = self.session.execute(stmt)
        return result.scalar_one_or_none() is not None
    
    async def document_exists_by_user_id(self, document: str, user_id: UUID) -> bool:
        """Check if document already exists"""
        stmt = select(LegalRepresentativeModel).where(
            LegalRepresentativeModel.document == document
            and LegalRepresentativeModel.id != user_id
        )
        result = self.session.execute(stmt)
        return result.scalar_one_or_none() is not None