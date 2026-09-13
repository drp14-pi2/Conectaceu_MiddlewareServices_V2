"""Legal representative degree model"""
from sqlalchemy import Column, String
from src.data.db_context.base import IntPkBaseModel

class LegalRepresentativeDegreeModel(IntPkBaseModel):
    __tablename__ = "legal_representative_degree"
    
    description = Column(String(50), unique=True, nullable=False)
