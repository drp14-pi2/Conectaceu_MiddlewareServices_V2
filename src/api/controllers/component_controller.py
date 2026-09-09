"""Course component controller"""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.application.services.course_component_service import CourseComponentService
from src.data.repositories.course_component_repository import CourseComponentRepository
from src.data.repositories.course_repository import CourseRepository
from src.data.db_context.database import get_db
from src.api.dependencies.auth_dependencies import get_current_active_user
from src.domain.schemas.course_component import CourseComponent, CourseComponentCreate
from src.domain.schemas.user import User

router = APIRouter(
    prefix="/component",
    tags=["Component"],
    dependencies=[Depends(get_current_active_user)]
)

def get_component_service(db: Session = Depends(get_db)) -> CourseComponentService:
    """Dependency injection for CourseComponentService"""
    repository = CourseComponentRepository(db)
    course_repository = CourseRepository(db)

    return CourseComponentService(repository, course_repository)


@router.post("/", response_model=CourseComponent, status_code=status.HTTP_201_CREATED)
async def create_component(
    dto: CourseComponentCreate,
    current_user: User = Depends(get_current_active_user),
    service: CourseComponentService = Depends(get_component_service)
):
    """Create a new course component. Admin (1), Coordinator (3), Educator (4) only."""
    if current_user.user_type_id not in [1, 3, 4]:
        raise HTTPException(status_code=403, detail="Não autorizado")
    
    try:
        return await service.create_component(dto)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/{component_id}/deactivate")
async def deactivate_component(
    component_id: UUID,
    current_user: User = Depends(get_current_active_user),
    service: CourseComponentService = Depends(get_component_service)
):
    """Deactivate a component. Admin (1), Coordinator (3), Educator (4) only."""
    if current_user.user_type_id not in [1, 3, 4]:
        raise HTTPException(status_code=403, detail="Não autorizado")
    
    try:
        result: bool = await service.deactivate_component(component_id)

        return {"message": "Componente desativado com sucesso", "success": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/{component_id}/activate")
async def activate_component(
    component_id: UUID,
    current_user: User = Depends(get_current_active_user),
    service: CourseComponentService = Depends(get_component_service)
):
    """Activate a component. Admin (1), Coordinator (3), Educator (4) only."""
    if current_user.user_type_id not in [1, 3, 4]:
        raise HTTPException(status_code=403, detail="Não autorizado")
    
    try:
        result: bool = await service.activate_component(component_id)

        return {"message": "Componente ativado com sucesso", "success": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/course/{course_id}", response_model=list[CourseComponent])
async def get_course_components(
    course_id: UUID,
    service: CourseComponentService = Depends(get_component_service)
):
    """Get all components for a course."""
    return await service.get_course_components(course_id)

@router.get("/{component_id}", response_model=CourseComponent)
async def get_component(
    component_id: UUID,
    service: CourseComponentService = Depends(get_component_service)
):
    """Get component by ID."""
    component: CourseComponent | None = await service.get_by_id(component_id)

    if not component:
        raise HTTPException(status_code=404, detail="Componente não encontrado")
    
    return component
