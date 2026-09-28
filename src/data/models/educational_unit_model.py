"""Educational unit model"""
from sqlalchemy import Column, String, Boolean
from src.data.db_context.base import UuidPkUpdatableBaseModel

class EducationalUnitModel(UuidPkUpdatableBaseModel):
    __tablename__ = 'educational_unit'

    name = Column(String(200), nullable=False)
    active = Column(Boolean, nullable=False, default=True)
    zip_code = Column(String(8), nullable=False)
    street = Column(String(200), nullable=False)
    number = Column(String(10), nullable=False)
    complement = Column(String(100), nullable=True)
    neighborhood = Column(String(100), nullable=False)
