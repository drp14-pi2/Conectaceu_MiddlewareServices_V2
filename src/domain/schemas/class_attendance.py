"""Class attendance schemas"""
from datetime import datetime
from uuid import UUID
from typing import Optional, List
from pydantic import BaseModel, ConfigDict

class AttendanceEntry(BaseModel):
    user_id: UUID
    attendance_type: int

class BulkAttendanceCreate(BaseModel):
    class_id: UUID
    attendances: List[AttendanceEntry]

class ClassAttendance(BaseModel):
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    class_id: UUID
    user_id: UUID
    attendance_type: int

    model_config = ConfigDict(from_attributes=True)

class ClassAttendanceCreate(ClassAttendance):
    pass

class AttendanceUpdate(BaseModel):
    attendance_type: int

class AttendanceSummary(BaseModel):
    total: int
    present: int
    in_other_group: int
    absent: int
    attendance_rate: float
