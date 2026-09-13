"""Class attendance model"""
from sqlalchemy import Column, Boolean, ForeignKey
from src.data.db_context.base import UuidPkUpdatableBaseModel
from src.data.db_context.types import UUIDBinary

class ClassAttendanceModel(UuidPkUpdatableBaseModel):
    __tablename__ = "class_attendance"
    
    attended = Column(Boolean, nullable=False, default=False)
    
    # Foreign keys
    user_id = Column(UUIDBinary, ForeignKey('user.id'), nullable=False)
    class_id = Column(UUIDBinary, ForeignKey('class.id'), nullable=False)
