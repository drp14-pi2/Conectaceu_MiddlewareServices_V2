"""Shift type model"""
from sqlalchemy import Column, String
from src.data.db_context.base import IntPkBaseModel

class ShiftTypeModel(IntPkBaseModel):
    __tablename__ = "shift_type"
    
    description = Column(String(50), unique=True, nullable=False)
