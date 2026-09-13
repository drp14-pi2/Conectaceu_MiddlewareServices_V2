"""User course enrollment model"""
from sqlalchemy import Column, Boolean, ForeignKey
from src.data.db_context.base import UuidPkUpdatableBaseModel
from src.data.db_context.types import UUIDBinary

class EnrollmentModel(UuidPkUpdatableBaseModel):
    __tablename__ = "enrollment"
    
    active = Column(Boolean, nullable=False, default=True)
    
    # Foreign keys
    user_id = Column(UUIDBinary, ForeignKey('user.id'), nullable=False)
    course_id = Column(UUIDBinary, ForeignKey('course.id'), nullable=False)
