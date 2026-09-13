"""Enrollment waiting list model"""
from sqlalchemy import Column, ForeignKey, DateTime, Integer, func
from src.data.db_context.base import Base
import uuid
from src.data.db_context.types import UUIDBinary

class EnrollmentWaitingListModel(Base):
    __tablename__ = "enrollment_waiting_list"
    
    id = Column(UUIDBinary, primary_key=True, default=lambda: uuid.uuid4())
    created_at = Column(DateTime, default=func.now(), nullable=False)
    user_id = Column(UUIDBinary, ForeignKey('user.id'), nullable=False)
    course_id = Column(UUIDBinary, ForeignKey('course.id'), nullable=False)
    position = Column(Integer, nullable=False) # Queue position
