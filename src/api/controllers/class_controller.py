"""Class controller"""
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from src.application.services.class_service import ClassService
from src.data.repositories.class_repository import ClassRepository
from src.data.repositories.course_component_repository import CourseComponentRepository
from src.data.repositories.course_repository import CourseRepository
from src.data.repositories.enrollment_repository import EnrollmentRepository
from src.data.db_context.database import get_db
from src.api.dependencies.auth_dependencies import get_current_active_user
from src.domain.schemas.class_ import Class, ClassBulkCreate, ClassFilter
from src.domain.schemas.user import User

router = APIRouter(
    prefix="/class",
    tags=["Class"],
    dependencies=[Depends(get_current_active_user)]
)

def get_class_service(db: Session = Depends(get_db)) -> ClassService:
    """Dependency injection for ClassService"""
    class_repo = ClassRepository(db)
    component_repo = CourseComponentRepository(db)
    enrollment_repo = EnrollmentRepository(db)
    course_repo = CourseRepository(db)

    return ClassService(class_repo, component_repo, enrollment_repo, course_repo)

@router.post("/", status_code=status.HTTP_201_CREATED)
async def bulk_create_classes(
    dto: ClassBulkCreate,
    current_user: User = Depends(get_current_active_user),
    service: ClassService = Depends(get_class_service)
):
    """Create multiple classes. Admin (1), Coordinator (3), Educator (4) only."""
    if current_user.user_type_id not in [1, 3, 4]:
        raise HTTPException(status_code=403, detail="Não autorizado")
    
    try:
        return await service.bulk_create_classes(dto)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.patch("/{class_id}/deactivate")
async def deactivate_class(
    class_id: UUID,
    current_user: User = Depends(get_current_active_user),
    service: ClassService = Depends(get_class_service)
):
    """Deactivate a class. Admin (1), Coordinator (3), Educator (4) only."""
    if current_user.user_type_id not in [1, 3, 4]:
        raise HTTPException(status_code=403, detail="Não autorizado")
    
    try:
        return await service.deactivate_class(class_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/{class_id}/activate")
async def activate_class(
    class_id: UUID,
    current_user: User = Depends(get_current_active_user),
    service: ClassService = Depends(get_class_service)
):
    """Activate a class. Admin (1), Coordinator (3), Educator (4) only."""
    if current_user.user_type_id not in [1, 3, 4]:
        raise HTTPException(status_code=403, detail="Não autorizado.")
    
    try:
        result: bool = await service.activate_class(class_id)

        return {"message": "Aula ativada com sucesso", "success": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=List[Class])
async def list_classes(
    component_id: UUID = Query(None),
    active: bool = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    service: ClassService = Depends(get_class_service)
):
    """List classes with filters."""
    filters: ClassFilter = ClassFilter(
        component_id=str(component_id) if component_id else None,
        active=active,
        page=page,
        page_size=page_size
    )

    return await service.find_classes(filters)


@router.get("/{class_id}", response_model=Class)
async def get_class(
    class_id: UUID,
    service: ClassService = Depends(get_class_service)
):
    """Get class by ID."""
    class_: Class | None = await service.get_by_id(class_id)

    if not class_:
        raise HTTPException(status_code=404, detail="Aula não encontrada")
    
    return class_
