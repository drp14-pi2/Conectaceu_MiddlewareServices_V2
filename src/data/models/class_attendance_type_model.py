"""User type model"""
from sqlalchemy import Column, String
from src.data.db_context.base import IntPkBaseModel

class ClassAttendanceTypeModel(IntPkBaseModel):
    __tablename__ = "class_attendance_type"

    description = Column(String(50), unique=True, nullable=False)
