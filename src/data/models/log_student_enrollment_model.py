"""Student enrollment logging model"""
from sqlalchemy import Column, String, Boolean, ForeignKey
from src.data.db_context.base import LogBaseModel
from src.data.db_context.types import UUIDBinary

class LogStudentEnrollmentModel(LogBaseModel):
    __tablename__ = "log_student_enrollment"
    
    enrolled = Column(Boolean, nullable=False)
    user_ip_address = Column(String(39), nullable=False)
    
    # Foreign keys
    user_id = Column(UUIDBinary, ForeignKey('user.id'), nullable=False)
    course_id = Column(UUIDBinary, ForeignKey('course.id'), nullable=False)
