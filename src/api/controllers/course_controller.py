"""Course controller"""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Request, status, Query
from sqlalchemy.orm import Session

from src.application.services.course_service import CourseService
from src.data.repositories.course_repository import CourseRepository
from src.data.repositories.course_component_repository import CourseComponentRepository
from src.data.db_context.database import get_db
from src.api.dependencies.auth_dependencies import get_current_active_user
from src.domain.schemas.course import Course, CourseCreate
from src.domain.schemas.user import User

router = APIRouter(
    prefix="/course",
    tags=["Course"],
    dependencies=[Depends(get_current_active_user)]
)

def get_course_service(db: Session = Depends(get_db)) -> CourseService:
    """Dependency injection for CourseService"""
    course_repo = CourseRepository(db)
    component_repo = CourseComponentRepository(db)

    return CourseService(course_repo, component_repo)

@router.post("/", response_model=Course, status_code=status.HTTP_201_CREATED)
async def create_course(
    request: Request,
    dto: CourseCreate,
    current_user: User = Depends(get_current_active_user),
    service: CourseService = Depends(get_course_service)
):
    """Create a new course with components. Admin (1), Coordinator (3), Educator (4) only."""
    if current_user.user_type_id not in [1, 3, 4]:
        raise HTTPException(status_code=403, detail="Não autorizado")
    
    try:
        user_ip: str = request.client.host if request.client else "unknown"

        return await service.create_course(
            dto,
            created_by_user_id=current_user.id,
            user_ip_address=user_ip
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.patch("/{course_id}/deactivate")
async def deactivate_course(
    course_id: UUID,
    current_user: User = Depends(get_current_active_user),
    service: CourseService = Depends(get_course_service)
):
    """Deactivate a course. Admin (1), Coordinator (3), Educator (4) only."""
    if current_user.user_type_id not in [1, 3, 4]:
        raise HTTPException(status_code=403, detail="Não autorizado")
    
    try:
        result: bool = await service.deactivate_course(course_id)

        return {'message': 'Curso desativado com sucesso', 'success': result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.patch("/{course_id}/activate")
async def activate_course(
    course_id: UUID,
    current_user: User = Depends(get_current_active_user),
    service: CourseService = Depends(get_course_service)
):
    """Activate a course. Admin (1), Coordinator (3), Educator (4) only."""
    if current_user.user_type_id not in [1, 3, 4]:
        raise HTTPException(status_code=403, detail="Não autorizado")
    
    try:
        result: bool = await service.activate_course(course_id)

        return {"message": "Curso ativado com sucesso", "success": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/", response_model=list[Course])
async def list_courses(
    name: str = Query(None),
    active: bool = Query(None),
    educator_id: UUID = Query(None),
    shift_type_id: int = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    service: CourseService = Depends(get_course_service)
):
    """List courses with filters."""
    return await service.find_courses(
        name=name,
        active=active,
        educator_id=str(educator_id) if educator_id else None,
        shift_type_id=shift_type_id,
        page=page,
        page_size=page_size
    )

@router.get("/{course_id}", response_model=Course)
async def get_course(
    course_id: UUID,
    service: CourseService = Depends(get_course_service)
):
    """Get course by ID."""
    course: Course | None = await service.get_by_id(course_id)

    if not course:
        raise HTTPException(status_code=404, detail="Curso não encontrado")
    
    return course

@router.get("/{course_id}/components", response_model=Course)
async def get_course_with_components(
    course_id: UUID,
    service: CourseService = Depends(get_course_service)
):
    """Get course with components."""
    try:
        return await service.get_course_with_components(course_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
