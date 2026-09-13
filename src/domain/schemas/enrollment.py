"""User course enrollment schemas"""
from datetime import datetime
from uuid import UUID
from typing import Optional, List
from pydantic import BaseModel, ConfigDict

class EnrollmentCreate(BaseModel):
    user_id: UUID
    course_id: UUID

class Enrollment(BaseModel):
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    user_id: UUID
    course_id: UUID
    active: bool

    model_config = ConfigDict(from_attributes=True)

class EnrollmentBulkCreate(BaseModel):
    course_id: UUID
    user_ids: List[UUID]

class EnrollmentSummary(BaseModel):
    user_id: UUID
    total_enrollments: int
    max_enrollments: int = 3
    remaining_slots: int
