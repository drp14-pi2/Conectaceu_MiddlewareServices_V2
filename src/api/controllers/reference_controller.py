"""Reference data controller for lookup tables"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.application.mappers.reference_mapper import ReferenceMapper
from src.data.repositories.legal_representative_degree_repository import LegalRepresentativeDegreeRepository
from src.data.repositories.user_sex_type_repository import UserSexTypeRepository
from src.data.repositories.user_gender_type_repository import UserGenderTypeRepository
from src.data.repositories.user_type_repository import UserTypeRepository
from src.data.repositories.document_type_repository import DocumentTypeRepository
from src.data.repositories.document_validation_status_type_repository import DocumentValidationStatusTypeRepository
from src.data.repositories.shift_type_repository import ShiftTypeRepository
from src.data.repositories.report_type_repository import ReportTypeRepository
from src.data.db_context.database import get_db
from src.api.dependencies.auth_dependencies import get_current_active_user

router = APIRouter(
    prefix="/reference",
    tags=["Reference"],
    dependencies=[Depends(get_current_active_user)]
)

# Sex Types
@router.get("/sex-types")
async def get_sex_types(db: Session = Depends(get_db)):
    """Get all sex types"""
    repo = UserSexTypeRepository(db)
    models = await repo.get_all()
    result = [ReferenceMapper.user_sex_type_model_to_schema(m) for m in models]
    result.sort(key=lambda x: x.id)

    return result

# Gender Types
@router.get("/gender-types")
async def get_gender_types(db: Session = Depends(get_db)):
    """Get all gender types"""
    repo = UserGenderTypeRepository(db)
    models = await repo.get_all()
    result = [ReferenceMapper.user_gender_type_model_to_schema(m) for m in models]
    result.sort(key=lambda x: x.id)

    return result

# User Types
@router.get("/user-types")
async def get_user_types(db: Session = Depends(get_db)):
    """Get all user types"""
    repo = UserTypeRepository(db)
    models = await repo.get_all()
    result = [ReferenceMapper.user_type_model_to_schema(m) for m in models]
    result.sort(key=lambda x: x.id)

    return result

# Legal Representative Degrees
@router.get("/legal-representative-degrees")
async def get_legal_representative_degrees(db: Session = Depends(get_db)):
    """Get all legal representative degrees"""
    repo = LegalRepresentativeDegreeRepository(db)
    models = await repo.get_all()
    result = [ReferenceMapper.legal_representative_degree_model_to_schema(m) for m in models]
    result.sort(key=lambda x: x.id)

    return result

# Document Types
@router.get("/document-types")
async def get_document_types(db: Session = Depends(get_db)):
    """Get all document types"""
    repo = DocumentTypeRepository(db)
    models = await repo.get_all()
    result = [ReferenceMapper.document_type_model_to_schema(m) for m in models]
    result.sort(key=lambda x: x.id)

    return result

# Validation Status Types
@router.get("/validation-status-types")
async def get_validation_status_types(db: Session = Depends(get_db)):
    """Get all validation status types"""
    repo = DocumentValidationStatusTypeRepository(db)
    models = await repo.get_all()
    result = [ReferenceMapper.document_validation_status_type_model_to_schema(m) for m in models]
    result.sort(key=lambda x: x.id)

    return result

# Shift Types
@router.get("/shift-types")
async def get_shift_types(db: Session = Depends(get_db)):
    """Get all shift types"""
    repo = ShiftTypeRepository(db)
    models = await repo.get_all()
    result = [ReferenceMapper.shift_type_model_to_schema(m) for m in models]
    result.sort(key=lambda x: x.id)

    return result

# Report Types
@router.get("/report-types")
async def get_report_types(db: Session = Depends(get_db)):
    """Get all report types"""
    repo = ReportTypeRepository(db)
    models = await repo.get_all()
    result = [ReferenceMapper.report_type_model_to_schema(m) for m in models]
    result.sort(key=lambda x: x.id)

    return result
