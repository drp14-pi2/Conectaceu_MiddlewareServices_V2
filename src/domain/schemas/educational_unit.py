"""Educational unit schemas"""
from datetime import datetime
from uuid import UUID
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

class EducationalUnitBase(BaseModel):
    name: str = Field(min_length=5, max_length=200)
    zip_code: str = Field(min_length=8, max_length=8)
    street: str = Field(min_length=3, max_length=200)
    number: str = Field(max_length=10)
    complement: Optional[str] = Field(None, max_length=100)
    neighborhood: str = Field(min_length=3, max_length=100)

class EducationalUnit(EducationalUnitBase):
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    active: bool

    model_config = ConfigDict(from_attributes=True)

class EducationalUnitCreate(EducationalUnitBase):
    pass

class EducationalUnitUpdate(BaseModel):
    name: str = Field(min_length=5, max_length=200)
    zip_code: Optional[str] = Field(None, min_length=8, max_length=8)
    street: Optional[str] = Field(None, min_length=3, max_length=200)
    number: Optional[str] = Field(None, max_length=10)
    complement: Optional[str] = Field(None, max_length=100)
    neighborhood: Optional[str] = Field(None, min_length=3, max_length=100)
    active: Optional[bool] = None
