"""Document request logging model"""
from sqlalchemy import Column, String, ForeignKey
from src.data.db_context.base import LogBaseModel
from src.data.db_context.types import UUIDBinary

class LogDocumentRequestModel(LogBaseModel):
    __tablename__ = "log_document_request"
    
    user_ip_address = Column(String(39), nullable=False)
    
    # Foreign keys
    document_id = Column(UUIDBinary, ForeignKey('document.id'), nullable=False)
    user_id = Column(UUIDBinary, ForeignKey('user.id'), nullable=False)
