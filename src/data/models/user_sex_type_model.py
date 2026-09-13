"""User sex type model"""
from sqlalchemy import Column, String
from src.data.db_context.base import IntPkBaseModel

class UserSexTypeModel(IntPkBaseModel):
  __tablename__ = "user_sex_type"
  
  description = Column(String(9), unique=True, nullable=False)
