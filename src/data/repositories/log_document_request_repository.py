"""Document request log repository - Insert only"""
from uuid import UUID

from sqlalchemy.orm import Session
from src.data.models.log_document_request_model import LogDocumentRequestModel
from src.data.repositories.base.base_repository import BaseRepository

class LogDocumentRequestRepository(BaseRepository):
    """Repository for Document Request logs - Insert only"""
    
    def __init__(self, session: Session):
        super().__init__(session, LogDocumentRequestModel)
    
    async def log(
        self,
        document_id: UUID,
        user_id: UUID,
        user_ip_address: str
    ) -> LogDocumentRequestModel:
        """Log a document request"""
        log = LogDocumentRequestModel(
            document_id=document_id,
            user_id=user_id,
            user_ip_address=user_ip_address
        )
        return await self.create(log)
