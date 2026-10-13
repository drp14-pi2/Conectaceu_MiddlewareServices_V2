"""Class attendance controller"""
from datetime import date
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.services.class_attendance_service import ClassAttendanceService
from src.application.services.security_service import SecurityService
from src.data.repositories.class_attendance_repository import ClassAttendanceRepository
from src.data.repositories.course_repository import CourseRepository
from src.data.repositories.document_repository import DocumentRepository
from src.data.repositories.legal_representative_repository import LegalRepresentativeRepository
from src.data.repositories.student_absence_justification_repository import StudentAbsenceJustificationRepository
from src.data.repositories.enrollment_repository import EnrollmentRepository
from src.data.repositories.class_repository import ClassRepository
from src.data.repositories.course_component_repository import CourseComponentRepository
from src.data.db_context.database import get_db
from src.api.dependencies.auth_dependencies import get_current_active_user
from src.data.repositories.user_repository import UserRepository
from src.domain.schemas.class_attendance import BulkAttendanceCreate
from src.domain.schemas.document import DocumentCreate
from src.domain.schemas.user import User
from src.api.middleware.rate_limiter import limiter

router = APIRouter(
    prefix="/attendance",
    tags=["Attendance"],
    dependencies=[Depends(get_current_active_user)]
)

def get_attendance_service(db: AsyncSession = Depends(get_db)) -> ClassAttendanceService:
    repository = ClassAttendanceRepository(db)
    enrollment_repo = EnrollmentRepository(db)
    class_repo = ClassRepository(db)
    component_repo = CourseComponentRepository(db)
    document_repo = DocumentRepository(db)
    absence_justification_repo = StudentAbsenceJustificationRepository(db)

    return ClassAttendanceService(
        repository,
        enrollment_repo,
        class_repo,
        component_repo,
        document_repo,
        absence_justification_repo
    )

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

@router.post("/class/take")
@limiter.limit("10/minute")
async def take_attendance(
    request: Request,
    dto: BulkAttendanceCreate,
    current_user: User = Depends(get_current_active_user),
    service: ClassAttendanceService = Depends(get_attendance_service),
    security_service: SecurityService = Depends(get_security_service)
):
    if await security_service.can_user_create_attendance(current_user.id, dto.class_id, dto.attendances):
        raise HTTPException(status_code=403, detail="Só pode interagir com seu próprio polo")
    
    """Take attendance for a class. Educators (4) and Coordinators (3) only."""
    if current_user.user_type_id not in [3, 4]:
        raise HTTPException(status_code=403, detail="Não autorizado")
    
    try:
        return await service.take_attendance(dto)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/class/{class_id}")
@limiter.limit("20/minute")
async def get_class_attendance(
    request: Request,
    class_id: UUID,
    current_user: User = Depends(get_current_active_user),
    service: ClassAttendanceService = Depends(get_attendance_service),
    security_service: SecurityService = Depends(get_security_service)
):
    if not await security_service.can_access_class(current_user.id, class_id):
        raise HTTPException(status_code=403, detail="Só pode interagir com seu próprio polo")
    
    """List attendances for a class. Educators (4) and Coordinators (3) only."""
    if current_user.user_type_id not in [3, 4]:
        raise HTTPException(status_code=403, detail="Não autorizado")
    
    """Get attendance for a class."""
    return await service.get_class_attendance(class_id)

@router.get("/user/{user_id}/class/{class_id}")
@limiter.limit("20/minute")
async def get_user_class_attendance(
    request: Request,
    user_id: UUID,
    class_id: UUID,
    current_user: User = Depends(get_current_active_user),
    service: ClassAttendanceService = Depends(get_attendance_service),
    security_service: SecurityService = Depends(get_security_service)
):
    """Get attendance summary for a user in a class."""
    if not await security_service.can_access_other_user(current_user.id, user_id):
        raise HTTPException(status_code=403, detail="Só pode interagir com seu próprio polo")

    if current_user.user_type_id not in [3, 4] and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Só pode ver sua própria presença")
    
    return await service.get_user_class_attendance(user_id, class_id)


@router.get("/user/{user_id}/classes")
@limiter.limit("20/minute")
async def get_user_classes(
    request: Request,
    user_id: UUID,
    date: Optional[date] = Query(None),
    attended: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    service: ClassAttendanceService = Depends(get_attendance_service),
    security_service: SecurityService = Depends(get_security_service)
):
    """Get all classes for a user with filters."""
    if not await security_service.can_access_other_user(current_user.id, user_id):
        raise HTTPException(status_code=403, detail="Só pode interagir com seu próprio polo")
    
    if current_user.user_type_id not in [3, 4] and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Só pode ver suas próprias aulas")
    
    return await service.get_user_classes(
        user_id=user_id,
        date=date,
        attended=attended,
        page=page,
        page_size=page_size
    )

@router.post("{attendance_id}/justify/user/{user_id}")
@limiter.limit("10/minute")
async def submit_absence_justification(
    request: Request,
    user_id: UUID,
    attendance_id: UUID,
    document: DocumentCreate,
    current_user: User = Depends(get_current_active_user),
    service: ClassAttendanceService = Depends(get_attendance_service),
    security_service: SecurityService = Depends(get_security_service)
):
    """
    Submit a justification document for an absence.
    """
    try:
        if not await security_service.can_access_other_user(current_user.id, user_id):
            raise HTTPException(status_code=403, detail="Só pode interagir com seu próprio polo")

        if current_user.user_type_id != 2 and current_user.id != user_id:
            raise HTTPException(status_code=403, detail="Só pode ver suas próprias aulas")
        
        return await service.submit_absence_justification(attendance_id, document, user_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
