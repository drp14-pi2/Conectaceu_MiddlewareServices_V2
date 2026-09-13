"""User address model"""
from sqlalchemy import Column, String, ForeignKey
from src.data.db_context.base import UuidPkUpdatableBaseModel
from src.data.db_context.types import UUIDBinary

class AddressModel(UuidPkUpdatableBaseModel):
    __tablename__ = "address"
    
    zip_code = Column(String(8), nullable=False)
    street = Column(String(200), nullable=False)
    number = Column(String(10), nullable=False)
    complement = Column(String(100), nullable=True)
    neighborhood = Column(String(100), nullable=False)
    
    # Foreign keys
    user_id = Column(UUIDBinary, ForeignKey('user.id'), nullable=False)
