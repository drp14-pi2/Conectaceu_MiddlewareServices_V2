"""User password history model"""
from sqlalchemy import Column, String, ForeignKey
from src.data.db_context.base import UuidPkBaseModel
from src.data.db_context.types import UUIDBinary

class UserPasswordHistoryModel(UuidPkBaseModel):
    __tablename__ = "user_password_history"
    
    password = Column(String(512), nullable=False)
    
    # Foreign keys
    user_id = Column(UUIDBinary, ForeignKey('user.id'), nullable=False)
