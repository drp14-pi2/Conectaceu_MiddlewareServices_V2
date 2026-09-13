"""Report request log repository - Insert only"""
from uuid import UUID

from sqlalchemy.orm import Session
from src.data.models.log_report_request_model import LogReportRequestModel
from src.data.repositories.base.base_repository import BaseRepository

class LogReportRequestRepository(BaseRepository):
    """Repository for Report Request logs - Insert only"""
    
    def __init__(self, session: Session):
        super().__init__(session, LogReportRequestModel)
    
    async def log(
        self,
        report_type_id: int,
        user_id: UUID,
        user_ip_address: str
    ) -> LogReportRequestModel:
        """Log a report request"""
        log = LogReportRequestModel(
            report_type_id=report_type_id,
            user_id=user_id,
            user_ip_address=user_ip_address
        )
        return await self.create(log)
