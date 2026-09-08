"""Document validation schemas"""
from datetime import datetime
from uuid import UUID
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from document import Document

class DocumentValidationInput(BaseModel):
    document_id: UUID
    document_validation_status_type_id: int = Field(ge=1, le=3)
    rejection_reason: Optional[str] = Field(None, max_length=500)

class DocumentValidation(BaseModel):
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    document_id: UUID
    document_validation_status_type_id: int
    rejection_reason: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class DocumentValidationWithDetails(DocumentValidation):
    document: Optional[Document] = None
    status_description: Optional[str] = None
