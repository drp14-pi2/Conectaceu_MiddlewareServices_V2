"""Document type model"""
from sqlalchemy import Column, String
from src.data.db_context.base import IntPkBaseModel

class DocumentTypeModel(IntPkBaseModel):
    __tablename__ = "document_type"
    
    description = Column(String(50), unique=True, nullable=False)
