"""Broadcast message log repository - Insert only"""
from uuid import UUID

from sqlalchemy.orm import Session
from src.data.models.log_broadcast_message_model import LogBroadcastMessageModel
from src.data.repositories.base.base_repository import BaseRepository

class LogBroadcastMessageRepository(BaseRepository):
    """Repository for Broadcast Message logs - Insert only"""
    
    def __init__(self, session: Session):
        super().__init__(session, LogBroadcastMessageModel)
    
    async def log(
        self,
        subject: str,
        message: str,
        document_1_file_name: str,
        document_1_base64: str,
        document_2_file_name: str,
        document_2_base64: str,
        sent_whatsapp: bool,
        sent_email: bool,
        sent_sms: bool,
        user_id: UUID,
        user_ip_address: str
    ) -> LogBroadcastMessageModel:
        """Log a broadcast message"""
        log = LogBroadcastMessageModel(
            subject=subject,
            message=message,
            document_1_file_name=document_1_file_name,
            document_1_base64=document_1_base64,
            document_2_file_name=document_2_file_name,
            document_2_base64=document_2_base64,
            sent_whatsapp=sent_whatsapp,
            sent_email=sent_email,
            sent_sms=sent_sms,
            user_id=user_id,
            user_ip_address=user_ip_address
        )
        return await self.create(log)
