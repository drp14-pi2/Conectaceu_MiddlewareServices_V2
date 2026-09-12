"""Class schemas"""
from datetime import datetime
from uuid import UUID
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator

class ClassBase(BaseModel):
    course_component_id: UUID
    date: datetime

class Class(ClassBase):
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    seats_in_use: int = 0
    active: bool = True

    model_config = ConfigDict(from_attributes=True)

class ClassCreate(ClassBase):
    pass

class ClassBulkCreate(BaseModel):
    course_component_id: str
    start_date: datetime
    end_date: datetime
    days_of_week: List[int] = Field(default=[0, 1, 2, 3, 4, 5, 6])
    seats_to_use: int = Field(5, ge=5)
    
    @field_validator('end_date')
    def end_after_start(cls, v, info):
        if 'start_date' in info.data and v < info.data['start_date']:
            raise ValueError('Data final deve ser posterior à data inicial')
        
        return v
    
    @field_validator('days_of_week')
    def days_received_in_range(cls, v):
        valid_days = {0, 1, 2, 3, 4, 5, 6}

        for day in v:
            if day not in valid_days:
                raise ValueError(f'{day} não é um dia da semana válido (0-6)')
            
        return v

class ClassUpdate(BaseModel):
    date: Optional[datetime] = None
    active: Optional[bool] = None

class ClassDetail(Class):
    course_id: Optional[UUID] = None
    component_name: Optional[str] = None
    available_seats: int = 0
    shift_type_id: Optional[int] = None

class ClassFilter(BaseModel):
    """DTO for filtering classes"""
    component_id: Optional[str] = None
    active: Optional[bool] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    page: int = Field(1, ge=1)
    page_size: int = Field(10, ge=1, le=100)
