"""Document validation model"""
from sqlalchemy import Column, Integer, String, ForeignKey
from src.data.db_context.base import UuidPkUpdatableBaseModel
from src.data.db_context.types import UUIDBinary

class DocumentValidationModel(UuidPkUpdatableBaseModel):
    __tablename__ = "document_validation"
    
    rejection_reason = Column(String(500), nullable=True)
    
    # Foreign keys
    document_validation_status_type_id = Column(Integer, ForeignKey('document_validation_status_type.id'), nullable=False)
    document_id = Column(UUIDBinary, ForeignKey('document.id'), nullable=False)
