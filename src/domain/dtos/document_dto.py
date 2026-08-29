"""DTOs for Document operations"""
from typing import Optional
from pydantic import BaseModel, Field

class DocumentCreateDTO(BaseModel):
    """DTO for uploading a document"""
    base64: str = Field(max_length=20_000_000)
    user_id: Optional[str] = None
    document_type_id: int
    is_front: Optional[bool] = None
    legal_representative_id: Optional[str] = None

class DocumentValidationDTO(BaseModel):
    """DTO for validating a document"""
    document_id: str
    document_validation_status_type_id: int
    rejection_reason: Optional[str] = Field(None, max_length=500)