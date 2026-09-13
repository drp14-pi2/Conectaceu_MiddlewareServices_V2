"""Student absence justification model - Links an attendance record to a justifying document"""
from sqlalchemy import Column, ForeignKey
from src.data.db_context.base import UuidPkBaseModel
from src.data.db_context.types import UUIDBinary

class StudentAbsenceJustificationModel(UuidPkBaseModel):
    __tablename__ = "student_absence_justification"

    class_attendance_id = Column(UUIDBinary, ForeignKey('class_attendance.id'), nullable=False)
    document_id = Column(UUIDBinary, ForeignKey('document.id'), nullable=False)
