"""Document type repository"""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.data.models.document_type_model import DocumentTypeModel
from src.data.repositories.base.base_repository import BaseRepository

class DocumentTypeRepository(BaseRepository):
    """Repository for Document Type reference entity"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, DocumentTypeModel)
    
    async def get_by_description(self, description: str) -> Optional[DocumentTypeModel]:
        """Get document type by description"""
        stmt = select(DocumentTypeModel).where(DocumentTypeModel.description == description)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()