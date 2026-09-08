"""Schemas for reference/lookup tables"""
from pydantic import BaseModel, ConfigDict, Field

# UserSexType
class UserSexTypeBase(BaseModel):
    description: str = Field(min_length=3, max_length=9)

class UserSexType(UserSexTypeBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

# UserGenderType
class UserGenderTypeBase(BaseModel):
    description: str = Field(min_length=3, max_length=20)

class UserGenderType(UserGenderTypeBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

# UserType
class UserTypeBase(BaseModel):
    description: str = Field(min_length=3, max_length=50)
    register_user: bool = False
    validate_user_documents: bool = False
    list_secretaries: bool = False
    list_educators: bool = False
    list_students: bool = False
    send_broadcast_message: bool = False
    add_courses: bool = False
    add_classes: bool = False

class UserType(UserTypeBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

# DocumentType
class DocumentTypeBase(BaseModel):
    description: str = Field(min_length=3, max_length=50)

class DocumentType(DocumentTypeBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

# DocumentValidationStatusType
class DocumentValidationStatusTypeBase(BaseModel):
    description: str = Field(min_length=3, max_length=50)

class DocumentValidationStatusType(DocumentValidationStatusTypeBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

# ShiftType
class ShiftTypeBase(BaseModel):
    description: str = Field(min_length=3, max_length=50)

class ShiftType(ShiftTypeBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

# ReportType
class ReportTypeBase(BaseModel):
    description: str = Field(min_length=3, max_length=50)

class ReportType(ReportTypeBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

# LegalRepresentativeDegree
class LegalRepresentativeDegreeBase(BaseModel):
    description: str = Field(min_length=3, max_length=50)

class LegalRepresentativeDegree(LegalRepresentativeDegreeBase):
    id: int
    model_config = ConfigDict(from_attributes=True)
