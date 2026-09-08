"""Legal representative schemas"""
from datetime import datetime
from uuid import UUID
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator
import re

class LegalRepresentativeBase(BaseModel):
    name: str = Field(min_length=3, max_length=200)
    document: str = Field(min_length=11, max_length=11)
    legal_representative_degree_id: int

    @field_validator('document')
    def validate_cpf(cls, v: str) -> str:
        cpf = re.sub(r'\D', '', v)
        if len(cpf) != 11:
            raise ValueError('CPF deve ter 11 dígitos')
        return cpf

class LegalRepresentativeCreate(LegalRepresentativeBase):
    user_id: UUID

class LegalRepresentative(LegalRepresentativeBase):
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    user_id: UUID

    model_config = ConfigDict(from_attributes=True)

class LegalRepresentativeUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=3, max_length=200)
    document: Optional[str] = Field(None, min_length=11, max_length=11)
    legal_representative_degree_id: Optional[int] = None
