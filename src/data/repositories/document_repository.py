"""Document repository"""
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import select

from src.data.models.document_model import DocumentModel
from src.data.repositories.base.base_repository import BaseRepository

class DocumentRepository(BaseRepository):
    """Repository for Document entity"""
    
    def __init__(self, session: Session):
        super().__init__(session, DocumentModel)
    
    async def get_by_user_id(self, user_id: UUID) -> List[DocumentModel]:
        """Get all documents for a user"""
        stmt = select(DocumentModel).where(DocumentModel.user_id == user_id and DocumentModel.legal_representative_id is None)
        result = self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def get_by_legal_representative_id(self, legal_representative_id: UUID) -> List[DocumentModel]:
        """Get all documents for a legal representative"""
        stmt = select(DocumentModel).where(DocumentModel.legal_representative_id == legal_representative_id)
        result = self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def get_latest_document(
        self,
        model: DocumentModel
    ) -> Optional[DocumentModel]:
        """Get the most recently created document matching the criteria"""
        stmt = (
            select(DocumentModel)
            .where(
                DocumentModel.user_id == model.user_id,
                DocumentModel.document_type_id == model.document_type_id,
                DocumentModel.is_front == model.is_front
            )
            .order_by(DocumentModel.created_at.desc())
            .limit(1)
        )
        
        result = self.session.execute(stmt)
        return result.scalars().first()
    
    async def get_by_type(
        self,
        user_id: UUID,
        document_type_id: int
    ) -> List[DocumentModel]:
        """Get documents of specific type for a user"""
        stmt = select(DocumentModel).where(
            DocumentModel.user_id == user_id,
            DocumentModel.document_type_id == document_type_id
        )
        result = self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def get_front_document(
        self,
        user_id: UUID,
        document_type_id: int
    ) -> Optional[DocumentModel]:
        """Get front side of a document type"""
        stmt = select(DocumentModel).where(
            DocumentModel.user_id == user_id,
            DocumentModel.document_type_id == document_type_id,
            DocumentModel.is_front == True
        )
        result = self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_back_document(
        self,
        user_id: UUID,
        document_type_id: int
    ) -> Optional[DocumentModel]:
        """Get back side of a document type"""
        stmt = select(DocumentModel).where(
            DocumentModel.user_id == user_id,
            DocumentModel.document_type_id == document_type_id,
            DocumentModel.is_front == False
        )
        result = self.session.execute(stmt)
        return result.scalar_one_or_none()
