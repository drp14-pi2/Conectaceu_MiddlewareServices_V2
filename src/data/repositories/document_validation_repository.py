"""Document validation repository"""
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import select

from src.data.models.document_validation_model import DocumentValidationModel
from src.data.repositories.base.base_repository import BaseRepository

class DocumentValidationRepository(BaseRepository):
    """Repository for Document Validation entity"""
    
    def __init__(self, session: Session):
        super().__init__(session, DocumentValidationModel)
    
    async def get_by_document_id(self, document_id: UUID) -> Optional[DocumentValidationModel]:
        """Get validation by document ID"""
        stmt = select(DocumentValidationModel).where(
            DocumentValidationModel.document_id == document_id
        )
        result = self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_by_status_type(
        self,
        status_type_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[DocumentValidationModel]:
        """Get validations by status type"""
        stmt = select(DocumentValidationModel).where(
            DocumentValidationModel.document_validation_status_type_id == status_type_id
        ).offset(skip).limit(limit)
        
        result = self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def get_pending_validations(self, skip: int = 0, limit: int = 100) -> List[DocumentValidationModel]:
        """Get pending validations (status_type_id = 1)"""
        return await self.get_by_status_type(1, skip, limit)
    
    async def get_approved_validations(self, skip: int = 0, limit: int = 100) -> List[DocumentValidationModel]:
        """Get approved validations (status_type_id = 2)"""
        return await self.get_by_status_type(2, skip, limit)
    
    async def get_rejected_validations(self, skip: int = 0, limit: int = 100) -> List[DocumentValidationModel]:
        """Get rejected validations (status_type_id = 3)"""
        return await self.get_by_status_type(3, skip, limit)
    
    async def update_status(
        self,
        validation_id: UUID,
        status_type_id: int,
        rejection_reason: Optional[str] = None
    ) -> bool:
        """Update validation status"""
        validation = await self.get_by_id(validation_id)
        if validation:
            validation.document_validation_status_type_id = status_type_id
            if rejection_reason:
                validation.rejection_reason = rejection_reason
            self.session.flush()
            return True
        return False