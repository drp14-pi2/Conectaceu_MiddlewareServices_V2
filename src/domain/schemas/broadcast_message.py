"""Broadcast message schemas"""
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator

class BroadcastMessageCreate(BaseModel):
    subject: str = Field(min_length=5, max_length=200)
    message: str = Field(min_length=1, max_length=4000)
    documents: List[BroadcastDocument] = Field(default_factory=list)
    send_email: bool = False
    send_whatsapp: bool = False
    send_sms: bool = False
    recipient_user_ids: Optional[List[str]] = None
    recipient_course_id: Optional[str] = None
    recipient_user_type_id: Optional[int] = None

    @field_validator('documents')
    def validate_documents(cls, v: List[str]) -> List[str]:
        if len(v) > 2:
            raise ValueError('Maximum of 2 documents allowed')
        for i, doc in enumerate(v):
            if len(doc) > 10_000_000:
                raise ValueError(f'Document {i+1} exceeds maximum size')
        return v

class BroadcastDocument(BaseModel):
    fileNameWithExtension: str = Field(min_length=5, max_length=144)
    fileBase64: str = Field(min_length=100, max_length=16_000_000)
