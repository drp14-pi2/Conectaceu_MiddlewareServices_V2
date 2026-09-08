"""User password history schemas"""
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict

class UserPasswordHistoryBase(BaseModel):
    id: UUID
    created_at: datetime
    password: str
    user_id: UUID
    
    model_config = ConfigDict(from_attributes=True)

class UserPasswordHistory(UserPasswordHistoryBase):
    pass

class UserPasswordHistoryCreate(UserPasswordHistoryBase):
    pass

class PasswordChange(BaseModel):
    new_password: str

    model_config = ConfigDict(from_attributes=True)
