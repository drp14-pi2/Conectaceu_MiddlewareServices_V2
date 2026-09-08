"""Document schemas"""
from datetime import datetime
from uuid import UUID
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

class DocumentBase(BaseModel):
    base64: str = Field(max_length=20_000_000)
    document_type_id: int
    is_front: Optional[bool] = None

class DocumentCreate(DocumentBase):
    user_id: Optional[UUID] = None
    legal_representative_id: Optional[UUID] = None

class Document(DocumentBase):
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    user_id: UUID
    legal_representative_id: Optional[UUID] = None

    model_config = ConfigDict(from_attributes=True)

class DocumentUpdate(BaseModel):
    is_front: Optional[bool] = None
