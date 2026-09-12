"""Student absence justification schemas"""
from datetime import datetime
from uuid import UUID
from typing import Optional
from pydantic import BaseModel, ConfigDict
from src.domain.schemas.document import DocumentCreate

class StudentAbsenceJustificationCreate(BaseModel):
    class_attendance_id: UUID
    document_id: UUID

class StudentAbsenceJustification(BaseModel):
    id: UUID
    created_at: datetime
    class_attendance_id: UUID
    document_id: Optional[UUID] = None

    model_config = ConfigDict(from_attributes=True)

class JustificationSubmit(BaseModel):
    attendance_id: UUID
    document: DocumentCreate
