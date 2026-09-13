"""Document validation status type repository"""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.data.models.document_validation_status_type_model import DocumentValidationStatusTypeModel
from src.data.repositories.base.base_repository import BaseRepository

class DocumentValidationStatusTypeRepository(BaseRepository):
    """Repository for Document Validation Status Type reference entity"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, DocumentValidationStatusTypeModel)
    
    async def get_by_description(self, description: str) -> Optional[DocumentValidationStatusTypeModel]:
        """Get validation status type by description"""
        stmt = select(DocumentValidationStatusTypeModel).where(
            DocumentValidationStatusTypeModel.description == description
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()