"""User schemas"""
from datetime import datetime, date
from uuid import UUID
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator
import re

from src.domain.schemas.address import AddressCreate

class UserBase(BaseModel):
    document: str = Field(min_length=11, max_length=11)
    name: str = Field(min_length=3, max_length=200)
    email: Optional[EmailStr] = None
    cellphone_number: Optional[str] = Field(None, pattern=r'^\d{8,11}$')
    contact_cellphone_number: Optional[str] = Field(None, pattern=r'^\d{8,11}$')
    birthdate: date
    school: Optional[str] = Field(None, max_length=200)
    sex_id: int
    gender_id: int

    @field_validator('document')
    def validate_cpf(cls, v: str) -> str:
        cpf = re.sub(r'\D', '', v)
        if len(cpf) != 11:
            raise ValueError('CPF deve ter 11 dígitos')
        return cpf

class UserCreate(UserBase):
    user_type_id: int
    password: str = Field(min_length=8, max_length=128)
    address: AddressCreate

class UserUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=3, max_length=200)
    email: Optional[EmailStr] = None
    cellphone_number: Optional[str] = Field(None, pattern=r'^\d{8,11}$')
    contact_cellphone_number: Optional[str] = Field(None, pattern=r'^\d{8,11}$')
    school: Optional[str] = Field(None, max_length=200)
    sex_id: Optional[int] = None
    gender_id: Optional[int] = None

class User(UserBase):
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    user_type_id: int
    active: bool
    email_verified: Optional[bool] = False

    model_config = ConfigDict(from_attributes=True)

    @property
    def age(self) -> int:
        today = date.today()
        return today.year - self.birthdate.year - (
            (today.month, today.day) < (self.birthdate.month, self.birthdate.day)
        )

    @property
    def is_minor(self) -> bool:
        return self.age < 18

    @property
    def is_over_70(self) -> bool:
        return self.age > 70

class UserList(BaseModel):
    id: UUID
    name: str
    email: Optional[EmailStr] = None
    user_type_id: int
    active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class UserDetail(User):
    """User with additional data for student listing"""
    sequential: Optional[int] = None

class DeactivateUser(BaseModel):
    reason: str = Field(min_length=10)
