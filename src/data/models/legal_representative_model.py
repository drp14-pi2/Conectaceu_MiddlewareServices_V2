"""Legal representative model for minor users"""
from sqlalchemy import Column, Integer, String, ForeignKey
from src.data.db_context.base import UuidPkUpdatableBaseModel
from src.data.db_context.types import UUIDBinary

class LegalRepresentativeModel(UuidPkUpdatableBaseModel):
    __tablename__ = "legal_representative"
    
    name = Column(String(200), nullable=False)
    document = Column(String(11), nullable=False)
    
    # Foreign keys
    user_id = Column(UUIDBinary, ForeignKey('user.id'), nullable=False)
    legal_representative_degree_id = Column(Integer, ForeignKey('legal_representative_degree.id'), nullable=False)
