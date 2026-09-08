"""Course component schemas"""
from datetime import datetime
from uuid import UUID
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

class CourseComponentBase(BaseModel):
    name: str = Field(min_length=3, max_length=100)
    description: str = Field(min_length=10, max_length=500)

class CourseComponentCreate(CourseComponentBase):
    course_id: UUID

class CourseComponent(CourseComponentBase):
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    course_id: UUID
    active: bool

    model_config = ConfigDict(from_attributes=True)

class CourseComponentUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=3, max_length=100)
    description: Optional[str] = Field(None, min_length=10, max_length=500)
    active: Optional[bool] = None
