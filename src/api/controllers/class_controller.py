"""Class controller"""
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.services.class_service import ClassService
from src.application.services.security_service import SecurityService
from src.data.repositories.class_repository import ClassRepository
from src.data.repositories.course_component_repository import CourseComponentRepository
from src.data.repositories.course_repository import CourseRepository
from src.data.repositories.document_repository import DocumentRepository
from src.data.repositories.enrollment_repository import EnrollmentRepository
from src.data.db_context.database import get_db
from src.api.dependencies.auth_dependencies import get_current_active_user
from src.data.repositories.legal_representative_repository import LegalRepresentativeRepository
from src.data.repositories.user_repository import UserRepository
from src.domain.schemas.class_ import Class, ClassBulkCreate, ClassFilter
from src.domain.schemas.user import User
from src.api.middleware.rate_limiter import limiter

router = APIRouter(
    prefix="/class",
    tags=["Class"],
    dependencies=[Depends(get_current_active_user)]
)

def get_class_service(db: AsyncSession = Depends(get_db)) -> ClassService:
    """Dependency injection for ClassService"""
    class_repo = ClassRepository(db)
    component_repo = CourseComponentRepository(db)
    enrollment_repo = EnrollmentRepository(db)
    course_repo = CourseRepository(db)

    return ClassService(class_repo, component_repo, enrollment_repo, course_repo)

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

@router.post("/", status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def bulk_create_classes(
    request: Request,
    dto: ClassBulkCreate,
    current_user: User = Depends(get_current_active_user),
    service: ClassService = Depends(get_class_service),
    security_service: SecurityService = Depends(get_security_service)
):
    """Create multiple classes. Admin (1), Coordinator (3), Educator (4) only."""
    if current_user.user_type_id not in [1, 3, 4]:
        raise HTTPException(status_code=403, detail="Não autorizado")

    if not await security_service.can_access_component(current_user.id, dto.course_component_id):
        raise HTTPException(status_code=403, detail="Só pode interagir com seu próprio polo")
    
    try:
        return await service.bulk_create_classes(dto)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.patch("/{class_id}/deactivate")
@limiter.limit("5/minute")
async def deactivate_class(
    request: Request,
    class_id: UUID,
    current_user: User = Depends(get_current_active_user),
    service: ClassService = Depends(get_class_service),
    security_service: SecurityService = Depends(get_security_service)
):
    """Deactivate a class. Admin (1), Coordinator (3), Educator (4) only."""
    if current_user.user_type_id not in [1, 3, 4]:
        raise HTTPException(status_code=403, detail="Não autorizado")

    if not await security_service.can_access_class(current_user.id, class_id):
        raise HTTPException(status_code=403, detail="Só pode interagir com seu próprio polo")
    
    try:
        return await service.deactivate_class(class_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.patch("/{class_id}/activate")
@limiter.limit("5/minute")
async def activate_class(
    request: Request,
    class_id: UUID,
    current_user: User = Depends(get_current_active_user),
    service: ClassService = Depends(get_class_service),
    security_service: SecurityService = Depends(get_security_service)
):
    """Activate a class. Admin (1), Coordinator (3), Educator (4) only."""
    if current_user.user_type_id not in [1, 3, 4]:
        raise HTTPException(status_code=403, detail="Não autorizado.")

    if not await security_service.can_access_class(current_user.id, class_id):
        raise HTTPException(status_code=403, detail="Só pode interagir com seu próprio polo")
    
    try:
        result: bool = await service.activate_class(class_id)

        return {"message": "Aula ativada com sucesso", "success": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/", response_model=List[Class])
@limiter.limit("20/minute")
async def list_classes(
    request: Request,
    dto: ClassFilter,
    current_user: User = Depends(get_current_active_user),
    service: ClassService = Depends(get_class_service),
    security_service: SecurityService = Depends(get_security_service)
):
    """List classes with filters."""
    if not await security_service.can_access_component(current_user.id, dto.component_id):
        raise HTTPException(status_code=403, detail="Só pode interagir com seu próprio polo")

    return await service.find_classes(dto)

@router.get("/{class_id}", response_model=Class)
@limiter.limit("20/minute")
async def get_class(
    request: Request,
    class_id: UUID,
    current_user: User = Depends(get_current_active_user),
    service: ClassService = Depends(get_class_service),
    security_service: SecurityService = Depends(get_security_service)
):
    """Get class by ID."""
    if not await security_service.can_access_class(current_user.id, class_id):
        raise HTTPException(status_code=403, detail="Só pode interagir com seu próprio polo")
    
    class_: Class | None = await service.get_by_id(class_id)

    if not class_:
        raise HTTPException(status_code=404, detail="Aula não encontrada")
    
    return class_
