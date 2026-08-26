"""Document controller"""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from src.application.services.document_service import DocumentService
from src.application.services.document_validation_service import DocumentValidationService
from src.data.repositories.address_repository import AddressRepository
from src.data.repositories.document_repository import DocumentRepository
from src.data.db_context.database import get_db
from src.api.dependencies.auth_dependencies import get_current_active_user
from src.data.repositories.document_validation_repository import DocumentValidationRepository
from src.data.repositories.legal_representative_repository import LegalRepresentativeRepository
from src.data.repositories.user_repository import UserRepository
from src.domain.dtos.document_dto import DocumentCreateDTO
from src.domain.dtos.document_validation_dto import DocumentValidationDTO
from src.domain.view_models.document_validation_view_model import DocumentValidationViewModel
from src.domain.view_models.document_view_model import DocumentViewModel
from src.domain.entities.user import User

router = APIRouter(
    prefix="/document",
    tags=["Document"],
    dependencies=[Depends(get_current_active_user)]
)


def get_document_service(db: Session = Depends(get_db)) -> DocumentService:
    """Dependency injection for DocumentService"""
    repository = DocumentRepository(db)
    user_repo = UserRepository(db)
    address_repo = AddressRepository(db)
    return DocumentService(repository, user_repo, address_repo)
    
    
def get_validation_service(db: Session = Depends(get_db)) -> DocumentValidationService:
    """Dependency injection for DocumentValidationService"""
    repository = DocumentValidationRepository(db)
    representative_repo = LegalRepresentativeRepository(db)
    return DocumentValidationService(repository, representative_repo)


@router.post("/", response_model=DocumentViewModel, status_code=status.HTTP_201_CREATED)
async def upload_document(
    dto: DocumentCreateDTO,
    current_user: User = Depends(get_current_active_user),
    service: DocumentService = Depends(get_document_service)
):
    """Upload a new document."""
    try:
        # Students can only upload their own documents
        if current_user.user_type_id == 5 and dto.user_id and current_user.id != dto.user_id:
            ValueError('Só pode enviar seus próprios documentos')
        return await service.upload_document(dto)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/user/{user_id}", response_model=List[DocumentViewModel])
async def get_user_documents(
    user_id: UUID,
    current_user: User = Depends(get_current_active_user),
    service: DocumentService = Depends(get_document_service)
):
    """
    Get all documents for a user.
    - Admin/Secretary can view any user's documents
    - Users can view their own documents
    """
    if current_user.user_type_id not in [1, 2] and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Só pode ver seus próprios documentos")
    
    return await service.get_user_documents(user_id)


@router.get("/{document_id}", response_model=DocumentViewModel)
async def get_document(
    request: Request,
    document_id: UUID,
    current_user: User = Depends(get_current_active_user),
    service: DocumentService = Depends(get_document_service)
):
    """Get document by ID."""
    user_ip = request.client.host if request.client else "unknown"
    document = await service.get_document_by_id(document_id, current_user.id, user_ip)
    if not document:
        raise HTTPException(status_code=404, detail="Nenhum documento encontrado")
    
    if current_user.user_type_id not in [1, 2] and document.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Só pode ver seus próprios documentos")
    
    return document

@router.get("/user/{user_id}/type/{document_type_id}", response_model=List[DocumentViewModel])
async def get_document_by_type(
    request: Request,
    user_id: UUID,
    document_type_id: int,
    current_user: User = Depends(get_current_active_user),
    service: DocumentService = Depends(get_document_service)
):
    """Get document by type."""
    user_ip = request.client.host if request.client else "unknown"
    documents = await service.get_documents_by_type(user_id, document_type_id, current_user.id, user_ip)
    if not documents:
        raise HTTPException(status_code=404, detail="Nenhum documento encontrado")
    
    if current_user.user_type_id not in [1, 2] and user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Só pode ver seus próprios documentos")
    
    return documents

@router.get("/management/type/{document_type_id}", response_model=dict)
async def get_management_document_template(
    document_type_id: int,
    component_id: Optional[UUID] = None,
    month: Optional[int] = None,
    current_user: User = Depends(get_current_active_user),
    service: DocumentService = Depends(get_document_service)
):
    """Get a management document template"""
    if current_user.user_type_id == 5:
        raise HTTPException(status_code=403, detail="Só equipe pode consultar estes documentos")
    
    document: dict = await service.get_management_document_template(document_type_id, component_id, month)

    if not document:
        raise HTTPException(status_code=404, detail="Nenhum documento encontrado")
    
    return document

# Document validation
@router.put("/validate", response_model=DocumentValidationViewModel)
async def validate_document(
    request: Request,
    dto: DocumentValidationDTO,
    current_user: User = Depends(get_current_active_user),
    service: DocumentValidationService = Depends(get_validation_service)
):
    """
    Validate a document (create or update validation).
    Admin (1) and Secretary (2) only.
    """
    if current_user.user_type_id not in [1, 2]:
        raise HTTPException(status_code=403, detail="Only administrators and secretaries can validate documents")
    
    try:
        user_ip = request.client.host if request.client else "unknown"
        return await service.create_or_update_validation(
            dto=dto,
            performed_by_user_id=current_user.id,
            user_ip_address=user_ip
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/validate/pending", response_model=list[DocumentValidationViewModel])
async def get_pending_validations(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    service: DocumentValidationService = Depends(get_validation_service)
):
    """Get pending document validations."""
    if current_user.user_type_id not in [1, 2]:
        raise HTTPException(status_code=403, detail="Only administrators and secretaries can list documents")
    return await service.get_pending_validations(skip, limit)