"""Course controller"""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Request, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.services.course_service import CourseService
from src.application.services.security_service import SecurityService
from src.data.repositories.class_repository import ClassRepository
from src.data.repositories.course_repository import CourseRepository
from src.data.repositories.course_component_repository import CourseComponentRepository
from src.data.repositories.document_repository import DocumentRepository
from src.data.repositories.educational_unit_repository import EducationalUnitRepository
from src.data.db_context.database import get_db
from src.api.dependencies.auth_dependencies import get_current_active_user
from src.data.repositories.enrollment_repository import EnrollmentRepository
from src.data.repositories.legal_representative_repository import LegalRepresentativeRepository
from src.data.repositories.user_repository import UserRepository
from src.domain.schemas.course import Course, CourseCreate, CourseList
from src.domain.schemas.user import User
from src.api.middleware.rate_limiter import limiter

router = APIRouter(
    prefix="/course",
    tags=["Course"],
    dependencies=[Depends(get_current_active_user)]
)

def get_course_service(db: AsyncSession = Depends(get_db)) -> CourseService:
    """Dependency injection for CourseService"""
    course_repo = CourseRepository(db)
    component_repo = CourseComponentRepository(db)
    educational_unit_repo = EducationalUnitRepository(db)

    return CourseService(course_repo, component_repo, educational_unit_repo)

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

@router.post("/", response_model=Course, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def create_course(
    request: Request,
    dto: CourseCreate,
    current_user: User = Depends(get_current_active_user),
    service: CourseService = Depends(get_course_service),
    security_service: SecurityService = Depends(get_security_service)
):
    """Create a new course with components. Admin (1), Coordinator (3), Educator (4) only."""
    if not await security_service.can_access_educational_unit(current_user.id, dto.educational_unit_id):
        raise HTTPException(status_code=403, detail="Só pode interagir com seu próprio polo")

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
@limiter.limit("5/minute")
async def deactivate_course(
    request: Request,
    course_id: UUID,
    current_user: User = Depends(get_current_active_user),
    service: CourseService = Depends(get_course_service),
    security_service: SecurityService = Depends(get_security_service)
):
    """Deactivate a course. Admin (1), Coordinator (3), Educator (4) only."""
    if not await security_service.can_access_course(current_user.id, course_id):
        raise HTTPException(status_code=403, detail="Só pode interagir com seu próprio polo")
    
    if current_user.user_type_id not in [1, 3, 4]:
        raise HTTPException(status_code=403, detail="Não autorizado")
    
    try:
        result: bool = await service.deactivate_course(course_id)

        return {'message': 'Curso desativado com sucesso', 'success': result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.patch("/{course_id}/activate")
@limiter.limit("5/minute")
async def activate_course(
    request: Request,
    course_id: UUID,
    current_user: User = Depends(get_current_active_user),
    service: CourseService = Depends(get_course_service),
    security_service: SecurityService = Depends(get_security_service)
):
    """Activate a course. Admin (1), Coordinator (3), Educator (4) only."""
    if not await security_service.can_access_course(current_user.id, course_id):
        raise HTTPException(status_code=403, detail="Só pode interagir com seu próprio polo")
    
    if current_user.user_type_id not in [1, 3, 4]:
        raise HTTPException(status_code=403, detail="Não autorizado")
    
    try:
        result: bool = await service.activate_course(course_id)

        return {"message": "Curso ativado com sucesso", "success": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/", response_model=list[Course])
@limiter.limit("20/minute")
async def list_courses(
    request: Request,
    name: str = Query(None),
    active: bool = Query(None),
    educator_id: UUID = Query(None),
    shift_type_id: int = Query(None),
    educational_unit_id: UUID = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    service: CourseService = Depends(get_course_service),
    security_service: SecurityService = Depends(get_security_service)
):
    """List courses with filters."""
    if educational_unit_id and not await security_service.can_access_educational_unit(current_user.id, educational_unit_id):
        raise HTTPException(status_code=403, detail="Só pode interagir com seu próprio polo")
    
    return await service.find_courses(
        name=name,
        active=active,
        educator_id=str(educator_id) if educator_id else None,
        shift_type_id=shift_type_id,
        educational_unit_id=educational_unit_id if educational_unit_id else current_user.educational_unit_id,
        page=page,
        page_size=page_size
    )

@router.get("/{course_id}", response_model=Course)
@limiter.limit("20/minute")
async def get_course(
    request: Request,
    course_id: UUID,
    current_user: User = Depends(get_current_active_user),
    service: CourseService = Depends(get_course_service),
    security_service: SecurityService = Depends(get_security_service)
):
    """Get course by ID."""
    if not await security_service.can_access_course(current_user.id, course_id):
        raise HTTPException(status_code=403, detail="Só pode interagir com seu próprio polo")
    
    course: Course | None = await service.get_by_id(course_id)

    if not course:
        raise HTTPException(status_code=404, detail="Curso não encontrado")
    
    return course

@router.get("/{course_id}/components", response_model=CourseList)
@limiter.limit("20/minute")
async def get_course_with_components(
    request: Request,
    course_id: UUID,
    current_user: User = Depends(get_current_active_user),
    service: CourseService = Depends(get_course_service),
    security_service: SecurityService = Depends(get_security_service)
):
    """Get course with components."""
    if not await security_service.can_access_course(current_user.id, course_id):
        raise HTTPException(status_code=403, detail="Só pode interagir com seu próprio polo")
    
    try:
        return await service.get_course_with_components(course_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
