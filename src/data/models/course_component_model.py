"""Course component model"""
from sqlalchemy import Column, String, Boolean, ForeignKey
from src.data.db_context.base import UuidPkUpdatableBaseModel
from src.data.db_context.types import UUIDBinary

class CourseComponentModel(UuidPkUpdatableBaseModel):
    __tablename__ = "course_component"
    
    name = Column(String(100), unique=True, nullable=False)
    description = Column(String(500), unique=True, nullable=False)
    active = Column(Boolean, nullable=False, default=True)
    
    # Foreign keys
    course_id = Column(UUIDBinary, ForeignKey('course.id'), nullable=False)
