"""Report controller"""
from http.client import HTTPException
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.services.report_service import ReportService
from src.application.services.security_service import SecurityService
from src.data.repositories.class_repository import ClassRepository
from src.data.repositories.course_component_repository import CourseComponentRepository
from src.data.repositories.course_repository import CourseRepository
from src.data.repositories.document_repository import DocumentRepository
from src.data.repositories.enrollment_repository import EnrollmentRepository
from src.data.repositories.legal_representative_repository import LegalRepresentativeRepository
from src.data.repositories.user_repository import UserRepository
from src.data.repositories.log_report_request_repository import LogReportRequestRepository
from src.data.db_context.database import get_db
from src.api.dependencies.auth_dependencies import get_current_active_user
from src.domain.schemas.user import User
from src.api.middleware.rate_limiter import limiter

router = APIRouter(
    prefix="/report",
    tags=["Report"],
    dependencies=[Depends(get_current_active_user)]
)

def get_report_service(db: AsyncSession = Depends(get_db)) -> ReportService:
    """Dependency injection for ReportService"""
    course_repo = CourseRepository(db)
    component_repo = CourseComponentRepository(db)
    enrollment_repo = EnrollmentRepository(db)
    user_repo = UserRepository(db)
    class_repo = ClassRepository(db)
    log_report_repo = LogReportRequestRepository(db)

    return ReportService(
        course_repo,
        component_repo,
        enrollment_repo,
        user_repo,
        class_repo,
        log_report_repo
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

@router.get("/students-by-course")
@limiter.limit("20/minute")
async def get_students_by_course(
    request: Request,
    course_id: Optional[UUID] = Query(None),
    component_id: Optional[UUID] = Query(None),
    educational_unit_id: Optional[UUID] = Query(None),
    current_user: User = Depends(get_current_active_user),
    service: ReportService = Depends(get_report_service),
    security_service: SecurityService = Depends(get_security_service)
):
    """Get students enrolled by course and/or component"""
    if current_user.user_type_id != 1 and not educational_unit_id:
        raise HTTPException(status_code=403, detail='ID do polo é obrigatório')

    if educational_unit_id and not await security_service.can_access_educational_unit(current_user.id, educational_unit_id):
        raise HTTPException(status_code=403, detail="Só pode interagir com seu próprio polo")
    
    user_ip: str = request.client.host if request.client else "unknown"

    return await service.get_students_by_course(
        course_id=course_id,
        component_id=component_id,
        educational_unit_id=educational_unit_id,
        requested_by_user_id=current_user.id,
        user_ip_address=user_ip
    )

@router.get("/course-vacancies")
@limiter.limit("20/minute")
async def get_course_vacancies(
    request: Request,
    course_id: Optional[UUID] = Query(None),
    educational_unit_id: Optional[UUID] = Query(None),
    current_user: User = Depends(get_current_active_user),
    service: ReportService = Depends(get_report_service),
    security_service: SecurityService = Depends(get_security_service)
):
    """Get vacancies by course"""
    if educational_unit_id and not await security_service.can_access_educational_unit(current_user.id, educational_unit_id):
        raise HTTPException(status_code=403, detail="Só pode interagir com seu próprio polo")
    
    user_ip: str = request.client.host if request.client else "unknown"
    
    return await service.get_course_vacancies(
        course_id=course_id,
        requested_by_user_id=current_user.id,
        educational_unit_id=educational_unit_id,
        user_ip_address=user_ip
    )
