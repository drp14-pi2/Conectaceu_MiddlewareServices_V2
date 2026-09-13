"""Report controller"""
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from src.application.services.report_service import ReportService
from src.data.repositories.class_repository import ClassRepository
from src.data.repositories.course_component_repository import CourseComponentRepository
from src.data.repositories.course_repository import CourseRepository
from src.data.repositories.enrollment_repository import EnrollmentRepository
from src.data.repositories.user_repository import UserRepository
from src.data.repositories.log_report_request_repository import LogReportRequestRepository
from src.data.db_context.database import get_db
from src.api.dependencies.auth_dependencies import get_current_active_user
from src.domain.schemas.user import User

router = APIRouter(
    prefix="/report",
    tags=["Report"],
    dependencies=[Depends(get_current_active_user)]
)

def get_report_service(db: Session = Depends(get_db)) -> ReportService:
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

@router.get("/students-by-course")
async def get_students_by_course(
    request: Request,
    course_id: Optional[UUID] = Query(None),
    component_id: Optional[UUID] = Query(None),
    current_user: User = Depends(get_current_active_user),
    service: ReportService = Depends(get_report_service)
):
    """Get students enrolled by course and/or component"""
    user_ip: str = request.client.host if request.client else "unknown"

    return await service.get_students_by_course(
        course_id=course_id,
        component_id=component_id,
        requested_by_user_id=current_user.id,
        user_ip_address=user_ip
    )

@router.get("/course-vacancies")
async def get_course_vacancies(
    request: Request,
    course_id: Optional[UUID] = Query(None),
    current_user: User = Depends(get_current_active_user),
    service: ReportService = Depends(get_report_service)
):
    """Get vacancies by course"""
    user_ip: str = request.client.host if request.client else "unknown"
    
    return await service.get_course_vacancies(
        course_id=course_id,
        requested_by_user_id=current_user.id,
        user_ip_address=user_ip
    )
