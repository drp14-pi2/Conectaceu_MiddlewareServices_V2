"""Document validation log repository - Insert only"""
from typing import Optional
from uuid import UUID
from sqlalchemy.orm import Session
from src.data.models.log_document_validation_model import LogDocumentValidationModel
from src.data.repositories.base.base_repository import BaseRepository

class LogDocumentValidationRepository(BaseRepository):
    """Repository for Document Validation logs - Insert only"""
    
    def __init__(self, session: Session):
        super().__init__(session, LogDocumentValidationModel)
    
    async def log(
        self,
        rejection_reason: Optional[str],
        activated: bool,
        user_id: UUID,
        performed_by_user_id: UUID,
        performed_user_ip_address: str
    ) -> LogDocumentValidationModel:
        """Log a document validation"""
        log = LogDocumentValidationModel(
            rejection_reason=rejection_reason,
            activated=activated,
            user_id=user_id,
            performed_by_user_id=performed_by_user_id,
            performed_user_ip_address=performed_user_ip_address
        )
        return await self.create(log)
