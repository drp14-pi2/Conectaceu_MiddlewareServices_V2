"""Document controller"""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.services.document_service import DocumentService
from src.application.services.document_validation_service import DocumentValidationService
from src.application.services.security_service import SecurityService
from src.data.repositories.address_repository import AddressRepository
from src.data.repositories.class_repository import ClassRepository
from src.data.repositories.course_component_repository import CourseComponentRepository
from src.data.repositories.course_repository import CourseRepository
from src.data.repositories.document_repository import DocumentRepository
from src.data.db_context.database import get_db
from src.api.dependencies.auth_dependencies import get_current_active_user
from src.data.repositories.document_validation_repository import DocumentValidationRepository
from src.data.repositories.enrollment_repository import EnrollmentRepository
from src.data.repositories.legal_representative_repository import LegalRepresentativeRepository
from src.data.repositories.user_repository import UserRepository
from src.domain.schemas.document import Document, DocumentCreate
from src.domain.schemas.document_validation import DocumentValidation, DocumentValidationInput
from src.data.repositories.log_document_request_repository import LogDocumentRequestRepository
from src.domain.schemas.user import User
from src.api.middleware.rate_limiter import limiter

router = APIRouter(
    prefix="/document",
    tags=["Document"]
)

def get_document_service(db: AsyncSession = Depends(get_db)) -> DocumentService:
    """Dependency injection for DocumentService"""
    repository = DocumentRepository(db)
    user_repo = UserRepository(db)
    address_repo = AddressRepository(db)
    log_doc_request_repo = LogDocumentRequestRepository(db)

    return DocumentService(repository, user_repo, address_repo, log_doc_request_repo)

def get_validation_service(db: AsyncSession = Depends(get_db)) -> DocumentValidationService:
    """Dependency injection for DocumentValidationService"""
    repository = DocumentValidationRepository(db)
    representative_repo = LegalRepresentativeRepository(db)
    doc_repo = DocumentRepository(db)

    return DocumentValidationService(repository, representative_repo, doc_repo)

def get_security_service(db: AsyncSession = Depends(get_db)) -> SecurityService:
    """Dependency injection for SecurityService"""
    class_repo = ClassRepository(db)
    component_repo = CourseComponentRepository(db)
    course_repo = CourseRepository(db)
    user_repo = UserRepository(db)
    document_repo = DocumentRepository(db)
    enrollment_repo = EnrollmentRepository(db)
    representative_repo = LegalRepresentativeRepository(db)

    return SecurityService(
        class_repo,
        component_repo,
        course_repo,
        user_repo,
        document_repo,
        enrollment_repo,
        representative_repo
    )

@router.post("/", response_model=Document, status_code=status.HTTP_201_CREATED)
@limiter.limit("15/minute")
async def upload_document(
    request: Request,
    dto: DocumentCreate,
    # TODO: remove commentary when user creation fixed
    #current_user: User = Depends(get_current_active_user),
    service: DocumentService = Depends(get_document_service),
    security_service: SecurityService = Depends(get_security_service)
):
    """Upload a new document."""
    # TODO: remove commentary when user creation fixed
    # if not await security_service.can_access_other_user(current_user.id, dto.user_id):
    #     raise HTTPException(status_code=403, detail="Só pode interagir com seu próprio polo")

    try:
    # TODO: remove commentary when user creation fixed
        # Students can only upload their own documents
        # if current_user.user_type_id == 5 and dto.user_id and current_user.id != dto.user_id:
        #     ValueError('Só pode enviar seus próprios documentos')

        return await service.upload_document(dto)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/user/{user_id}", response_model=List[Document])
@limiter.limit("20/minute")
async def get_user_documents(
    request: Request,
    user_id: UUID,
    current_user: User = Depends(get_current_active_user),
    service: DocumentService = Depends(get_document_service),
    security_service: SecurityService = Depends(get_security_service)
):
    """
    Get all documents for a user.
    - Admin/Secretary can view any user's documents
    - Users can view their own documents
    """
    if not await security_service.can_access_other_user(current_user.id, user_id):
        raise HTTPException(status_code=403, detail="Só pode interagir com seu próprio polo")
    
    if current_user.user_type_id not in [1, 2] and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Só pode ver seus próprios documentos")
    
    return await service.get_user_documents(user_id)

@router.get("/{document_id}", response_model=Document)
@limiter.limit("20/minute")
async def get_document(
    request: Request,
    document_id: UUID,
    current_user: User = Depends(get_current_active_user),
    service: DocumentService = Depends(get_document_service),
    security_service: SecurityService = Depends(get_security_service)
):
    """Get document by ID."""
    if not await security_service.can_access_document(current_user.id, document_id):
        raise HTTPException(status_code=403, detail="Só pode interagir com seu próprio polo")

    user_ip: str = request.client.host if request.client else "unknown"
    document: Document | None = await service.get_document_by_id(document_id, current_user.id, user_ip)

    if not document:
        raise HTTPException(status_code=404, detail="Nenhum documento encontrado")
    
    if current_user.user_type_id not in [1, 2] and document.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Só pode ver seus próprios documentos")
    
    return document

@router.get("/user/{user_id}/type/{document_type_id}", response_model=List[Document])
@limiter.limit("20/minute")
async def get_document_by_type(
    request: Request,
    user_id: UUID,
    document_type_id: int,
    current_user: User = Depends(get_current_active_user),
    service: DocumentService = Depends(get_document_service),
    security_service: SecurityService = Depends(get_security_service)
):
    """Get document by type."""
    if not await security_service.can_access_other_user(current_user.id, user_id):
        raise HTTPException(status_code=403, detail="Só pode interagir com seu próprio polo")
    
    user_ip: str = request.client.host if request.client else "unknown"
    documents: List[Document] = await service.get_documents_by_type(user_id, document_type_id, current_user.id, user_ip)

    if not documents:
        raise HTTPException(status_code=404, detail="Nenhum documento encontrado")
    
    if current_user.user_type_id not in [1, 2] and user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Só pode ver seus próprios documentos")
    
    return documents

@router.get("/management/type/{document_type_id}", response_model=dict)
@limiter.limit("20/minute")
async def get_management_document_template(
    request: Request,
    document_type_id: int,
    component_id: Optional[UUID] = None,
    month: Optional[int] = None,
    current_user: User = Depends(get_current_active_user),
    service: DocumentService = Depends(get_document_service)
):
    """Get a management document template"""
    if current_user.user_type_id == 5:
        raise HTTPException(status_code=403, detail="Só equipe pode consultar estes documentos")
    
    document: dict[str, str] | None = await service.get_management_document_template(document_type_id, component_id, month)

    if not document:
        raise HTTPException(status_code=404, detail="Nenhum documento encontrado")
    
    return document

# Document validation
@router.put("/validate", response_model=DocumentValidation)
@limiter.limit("5/minute")
async def validate_document(
    request: Request,
    dto: DocumentValidationInput,
    current_user: User = Depends(get_current_active_user),
    service: DocumentValidationService = Depends(get_validation_service),
    security_service: SecurityService = Depends(get_security_service)
):
    """
    Validate a document (create or update validation).
    Admin (1) and Secretary (2) only.
    """
    if not await security_service.can_access_document(current_user.id, dto.document_id):
        raise HTTPException(status_code=403, detail="Só pode interagir com seu próprio polo")
    
    if current_user.user_type_id not in [1, 2]:
        raise HTTPException(status_code=403, detail="Não autorizado")
    
    try:
        user_ip: str = request.client.host if request.client else "unknown"

        return await service.create_or_update_validation(
            dto=dto,
            performed_by_user_id=current_user.id,
            user_ip_address=user_ip
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/validate/pending", response_model=list[DocumentValidation])
@limiter.limit("20/minute")
async def get_pending_validations(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    service: DocumentValidationService = Depends(get_validation_service)
):
    """Get pending document validations."""
    if current_user.user_type_id not in [1, 2]:
        raise HTTPException(status_code=403, detail="Não autorizado")
    
    return await service.get_pending_validations(current_user.educational_unit_id, skip, limit)
