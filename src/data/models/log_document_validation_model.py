"""Document validation logging model"""
from sqlalchemy import Column, String, Boolean, ForeignKey
from src.data.db_context.base import LogBaseModel
from src.data.db_context.types import UUIDBinary

class LogDocumentValidationModel(LogBaseModel):
    __tablename__ = "log_document_validation"
    
    rejection_reason = Column(String(500), nullable=True)
    activated = Column(Boolean, nullable=False)
    performed_user_ip_address = Column(String(39), nullable=False)
    
    # Foreign keys
    user_id = Column(UUIDBinary, ForeignKey('user.id'), nullable=False)
    performed_by_user_id = Column(UUIDBinary, ForeignKey('user.id'), nullable=False)
