"""Class model"""
from sqlalchemy import Column, DateTime, Integer, Boolean, ForeignKey
from src.data.db_context.base import UuidPkUpdatableBaseModel
from src.data.db_context.types import UUIDBinary

class ClassModel(UuidPkUpdatableBaseModel):
    __tablename__ = "class"
    
    seats_in_use = Column(Integer, nullable=False, default=0)
    active = Column(Boolean, nullable=False, default=True)
    date = Column(DateTime, nullable=False)
    
    # Foreign keys
    course_component_id = Column(UUIDBinary, ForeignKey('course_component.id'), nullable=False)
