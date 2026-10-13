"""Address controller"""
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.services.address_service import AddressService
from src.application.services.security_service import SecurityService
from src.data.repositories.address_repository import AddressRepository
from src.data.db_context.database import get_db
from src.api.dependencies.auth_dependencies import get_current_active_user
from src.data.repositories.class_repository import ClassRepository
from src.data.repositories.course_component_repository import CourseComponentRepository
from src.data.repositories.course_repository import CourseRepository
from src.data.repositories.document_repository import DocumentRepository
from src.data.repositories.enrollment_repository import EnrollmentRepository
from src.data.repositories.legal_representative_repository import LegalRepresentativeRepository
from src.data.repositories.user_repository import UserRepository
from src.domain.schemas.address import Address, AddressUpdate
from src.domain.schemas.user import User
from src.api.middleware.rate_limiter import limiter

router = APIRouter(
    prefix="/address",
    tags=["Address"],
    dependencies=[Depends(get_current_active_user)]
)

def get_address_service(db: AsyncSession = Depends(get_db)) -> AddressService:
    """Dependency injection for AddressService"""
    repository = AddressRepository(db)

    return AddressService(repository)

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

@router.get("/user/{user_id}", response_model=List[Address])
@limiter.limit("20/minute")
async def get_user_addresses(
    request: Request,
    user_id: UUID,
    current_user: User = Depends(get_current_active_user),
    service: AddressService = Depends(get_address_service),
    security_service: SecurityService = Depends(get_security_service)
):
    """
    Get all addresses for a user.
    - Users can view their own addresses
    - Admin/Secretary can view any user's addresses
    - Others: 403
    """
    if not await security_service.can_access_other_user(current_user.id, user_id):
        raise HTTPException(status_code=403, detail="Só pode interagir com seu próprio polo")

    # Admin (1) and Secretary (2) can view any. Users can only view their own
    if current_user.user_type_id in [1, 2] or current_user.id == user_id:
        return await service.get_user_addresses(user_id)
    
    raise HTTPException(status_code=403, detail="Só pode ver seu próprio endereço")

@router.put("/{address_id}", response_model=Address)
@limiter.limit("10/minute")
async def update_address(
    request: Request,
    address_id: UUID,
    dto: AddressUpdate,
    current_user: User = Depends(get_current_active_user),
    service: AddressService = Depends(get_address_service),
    security_service: SecurityService = Depends(get_security_service)
):
    """Update an address"""
    try:
        existing: Address | None = await service.get_by_id(address_id)

        if not existing:
            raise HTTPException(status_code=404, detail="Endereço não encontrado")

        if not await security_service.can_access_other_user(current_user.id, existing.user_id):
            raise HTTPException(status_code=403, detail="Só pode interagir com seu próprio polo")
        
        # Admin/Secretary can update any. Users can only update their own
        if current_user.user_type_id in [1, 2] or existing.user_id == current_user.id:
            return await service.update_address(address_id, dto)
        
        raise HTTPException(status_code=403, detail="Só pode atualizar seu próprio endereço")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
