"""User gender type model"""
from sqlalchemy import Column, String
from src.data.db_context.base import IntPkBaseModel

class UserGenderTypeModel(IntPkBaseModel):
    __tablename__ = "user_gender_type"

    description = Column(String(30), unique=True, nullable=False)
