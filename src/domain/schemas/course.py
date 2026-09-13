"""Course schemas"""
from datetime import datetime
from uuid import UUID
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field
from src.domain.schemas.course_component import CourseComponent

class CourseBase(BaseModel):
    name: str = Field(min_length=3, max_length=100)
    total_seat_limit: int = Field(ge=1)
    workload: int = Field(ge=1)
    min_student_age: int = Field(ge=1)
    max_student_age: int = Field(ge=1)
    shift_type_id: int = Field(ge=1)

class CourseCreate(CourseBase):
    responsible_educator_1: UUID
    responsible_educator_2: Optional[UUID] = None

class Course(CourseBase):
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    responsible_educator_1: UUID
    responsible_educator_2: Optional[UUID] = None
    active: bool

    model_config = ConfigDict(from_attributes=True)

class CourseUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=3, max_length=100)
    total_seat_limit: Optional[int] = Field(None, ge=1)
    workload: Optional[int] = Field(None, ge=1)
    shift_type_id: Optional[int] = None
    responsible_educator_1: Optional[UUID] = None
    responsible_educator_2: Optional[UUID] = None
    active: Optional[bool] = None

class CourseList(BaseModel):
    id: UUID
    name: str
    workload: int
    active: bool
    shift_type_id: int
    total_seat_limit: int
    components: List[CourseComponent]

    model_config = ConfigDict(from_attributes=True)
