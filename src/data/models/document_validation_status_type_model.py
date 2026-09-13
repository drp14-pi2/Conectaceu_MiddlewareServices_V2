"""Document validation status type model"""
from sqlalchemy import Column, String
from src.data.db_context.base import IntPkBaseModel

class DocumentValidationStatusTypeModel(IntPkBaseModel):
    __tablename__ = "document_validation_status_type"
    
    description = Column(String(50), unique=True, nullable=False)
