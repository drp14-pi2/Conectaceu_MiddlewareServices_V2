"""Class attendance model"""
from sqlalchemy import Column, Boolean, Integer, ForeignKey
from src.data.db_context.base import UuidPkUpdatableBaseModel
from src.data.db_context.types import UUIDBinary

class ClassAttendanceModel(UuidPkUpdatableBaseModel):
    __tablename__ = "class_attendance"
    
    # Foreign keys
    user_id = Column(UUIDBinary, ForeignKey('user.id'), nullable=False)
    class_id = Column(UUIDBinary, ForeignKey('class.id'), nullable=False)
    class_attendance_type_id = Column(Integer, ForeignKey('class_attendance_type.id'), nullable=False)
