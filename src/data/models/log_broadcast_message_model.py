"""Broadcast message logging model"""
from sqlalchemy import Column, String, Boolean, ForeignKey, Text
from sqlalchemy.dialects.mysql import MEDIUMTEXT
from src.data.db_context.base import LogBaseModel
from src.data.db_context.types import UUIDBinary

class LogBroadcastMessageModel(LogBaseModel):
    __tablename__ = "log_broadcast_message"
    
    subject = Column(String(40), nullable=False)
    message = Column(Text, nullable=False)
    document_1_file_name = Column(String(30), nullable=False)
    document_1_base64 = Column(MEDIUMTEXT, nullable=False)
    document_2_file_name = Column(String(30), nullable=False)
    document_2_base64 = Column(MEDIUMTEXT, nullable=False)
    sent_whatsapp = Column(Boolean, nullable=False, default=False)
    sent_email = Column(Boolean, nullable=False, default=False)
    sent_sms = Column(Boolean, nullable=False, default=False)
    user_ip_address = Column(String(39), nullable=False)
    
    # Foreign keys
    user_id = Column(UUIDBinary, ForeignKey('user.id'), nullable=False)
