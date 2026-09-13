"""Document model"""
from sqlalchemy import Column, Boolean, ForeignKey, Integer
from sqlalchemy.dialects.mysql import MEDIUMTEXT
from src.data.db_context.base import UuidPkUpdatableBaseModel
from src.data.db_context.types import UUIDBinary

class DocumentModel(UuidPkUpdatableBaseModel):
    __tablename__ = "document"
    
    base64 = Column(MEDIUMTEXT, nullable=False)
    is_front = Column(Boolean, nullable=True)
    
    # Foreign keys
    user_id = Column(UUIDBinary, ForeignKey('user.id'), nullable=False)
    document_type_id = Column(Integer, ForeignKey('document_type.id'), nullable=False)
    legal_representative_id = Column(UUIDBinary, ForeignKey('legal_representative.id'), nullable=True)
