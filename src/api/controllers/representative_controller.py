"""Legal representative controller"""
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.application.services.legal_representative_service import LegalRepresentativeService
from src.data.repositories.document_repository import DocumentRepository
from src.data.repositories.document_validation_repository import DocumentValidationRepository
from src.data.repositories.legal_representative_repository import LegalRepresentativeRepository
from src.data.db_context.database import get_db
from src.api.dependencies.auth_dependencies import get_current_active_user
from src.data.repositories.user_repository import UserRepository
from src.domain.schemas.legal_representative import LegalRepresentative, LegalRepresentativeCreate, LegalRepresentativeUpdate
from src.domain.schemas.user import User

router = APIRouter(
    prefix="/representative",
    tags=["Representative"],
    dependencies=[Depends(get_current_active_user)]
)

def get_representative_service(db: Session = Depends(get_db)) -> LegalRepresentativeService:
    """Dependency injection for LegalRepresentativeService"""
    repository = LegalRepresentativeRepository(db)
    document_repo = DocumentRepository(db)
    document_validation_repo = DocumentValidationRepository(db)
    user_repo = UserRepository(db)

    return LegalRepresentativeService(repository, document_repo, document_validation_repo, user_repo)

@router.post("/", response_model=LegalRepresentative, status_code=status.HTTP_201_CREATED)
async def create_representative(
    dto: LegalRepresentativeCreate,
    current_user: User = Depends(get_current_active_user),
    service: LegalRepresentativeService = Depends(get_representative_service)
):
    """Create a new legal representative. Admin (1) and Secretary (2) only."""
    if current_user.user_type_id not in [1, 2]:
        raise HTTPException(status_code=403, detail="Não autorizado")
    
    try:
        return await service.create_representative(dto)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/{representative_id}", response_model=LegalRepresentative)
async def update_representative(
    representative_id: UUID,
    dto: LegalRepresentativeUpdate,
    current_user: User = Depends(get_current_active_user),
    service: LegalRepresentativeService = Depends(get_representative_service)
):
    """Update a legal representative. Admin (1) and Secretary (2) only."""
    if current_user.user_type_id not in [1, 2]:
        raise HTTPException(status_code=403, detail="Não autorizado")
    
    try:
        representative: LegalRepresentative | None = await service.update_representative(representative_id, dto)

        if not representative:
            raise HTTPException(status_code=404, detail="Representante legal não encontrado")
        
        return representative
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{representative_id}")
async def delete_representative(
    representative_id: UUID,
    current_user: User = Depends(get_current_active_user),
    service: LegalRepresentativeService = Depends(get_representative_service)
):
    """Delete a legal representative. Admin (1), Secretary (2) and Student (5) only."""
    if current_user.user_type_id not in [1, 2, 5]:
        raise HTTPException(status_code=403, detail="Não autorizado")
    
    result: bool = await service.delete_representative(representative_id)

    if not result:
        raise HTTPException(status_code=404, detail="Representante não pôde ser excluído")
    
    return {"message": "Representante excluído com sucesso"}

@router.get("/user/{user_id}", response_model=List[LegalRepresentative])
async def get_user_representatives(
    user_id: UUID,
    current_user: User = Depends(get_current_active_user),
    service: LegalRepresentativeService = Depends(get_representative_service)
):
    """
    Get all legal representatives for a user.
    - Admin/Secretary can view any
    - Users can view their own
    """
    if current_user.user_type_id not in [1, 2] and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Só pode ver seus próprios representantes")
    
    return await service.get_user_representatives(user_id)

@router.get("/{representative_id}", response_model=LegalRepresentative)
async def get_representative(
    representative_id: UUID,
    current_user: User = Depends(get_current_active_user),
    service: LegalRepresentativeService = Depends(get_representative_service)
):
    """Get representative by ID."""
    representative: LegalRepresentative | None = await service.get_by_id(representative_id)

    if not representative:
        raise HTTPException(status_code=404, detail="Representante não encontrado")
    
    # Check ownership
    if current_user.user_type_id not in [1, 2] and representative.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Só pode ver seus próprios representantes")
    
    return representative
