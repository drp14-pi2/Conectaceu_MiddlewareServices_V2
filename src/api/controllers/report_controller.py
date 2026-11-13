"""Report controller"""
import base64
from http.client import HTTPException
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query, Request, Response
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
from src.infrastructure.xlsx.xlsx_render_service import XlsxRenderService

router = APIRouter(
    prefix="/report",
    tags=["Report"],
    dependencies=[Depends(get_current_active_user)]
)

STUDENTS_COLUMNS = {
    "course_name": "Curso",
    "shift_type_id": "Turno",
    "student_name": "Aluno",
    "student_document": "Documento",
    "student_phone": "Celular",
    "student_email": "E-mail"
}

VACANCIES_COLUMNS = {
    "course_name": "Curso",
    "total_seats": "Total de vagas",
    "enrolled": "Alunos matriculados",
    "available_seats": "Vagas abertas",
    "occupation_rate": "Taxa de ocupação"
}

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
        educational_unit_id=educational_unit_id,
        requested_by_user_id=current_user.id,
        user_ip_address=user_ip
    )

@router.get("/students-by-course/xlsx")
@limiter.limit("10/minute")
async def export_students_by_course_xlsx(
    request: Request,
    course_id: Optional[UUID] = Query(None),
    educational_unit_id: Optional[UUID] = Query(None),
    current_user: User = Depends(get_current_active_user),
    service: ReportService = Depends(get_report_service),
    security_service: SecurityService = Depends(get_security_service),
):
    """Export students-by-course report as XLSX"""
    if current_user.user_type_id != 1 and not educational_unit_id:
        raise HTTPException(403, "ID do polo é obrigatório")

    if educational_unit_id and not await security_service.can_access_educational_unit(current_user.id, educational_unit_id):
        raise HTTPException(403, "Só pode interagir com seu próprio polo")

    user_ip = request.client.host if request.client else "unknown"
    rows = await service.get_students_by_course(
        course_id=course_id,
        educational_unit_id=educational_unit_id,
        requested_by_user_id=current_user.id,
        user_ip_address=user_ip,
    )
    xlsx = XlsxRenderService.render_to_base64(
        rows,
        sheet_name="Alunos por curso",
        column_labels=STUDENTS_COLUMNS,
        column_order=list(STUDENTS_COLUMNS.keys()),
    )

    return Response(
        content=base64.b64decode(xlsx),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="alunos_por_curso.xlsx"'},
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
    if current_user.user_type_id != 1 and not educational_unit_id:
        raise HTTPException(status_code=403, detail='ID do polo é obrigatório')
    
    if educational_unit_id and not await security_service.can_access_educational_unit(current_user.id, educational_unit_id):
        raise HTTPException(status_code=403, detail="Só pode interagir com seu próprio polo")
    
    user_ip: str = request.client.host if request.client else "unknown"
    
    return await service.get_course_vacancies(
        course_id=course_id,
        requested_by_user_id=current_user.id,
        educational_unit_id=educational_unit_id,
        user_ip_address=user_ip
    )

@router.get("/course-vacancies/xlsx")
@limiter.limit("10/minute")
async def export_course_vacancies_xlsx(
    request: Request,
    course_id: Optional[UUID] = Query(None),
    educational_unit_id: Optional[UUID] = Query(None),
    current_user: User = Depends(get_current_active_user),
    service: ReportService = Depends(get_report_service),
    security_service: SecurityService = Depends(get_security_service),
):
    """Export course-vacancies report as XLSX"""
    if current_user.user_type_id != 1 and not educational_unit_id:
        raise HTTPException(403, "ID do polo é obrigatório")

    if educational_unit_id and not await security_service.can_access_educational_unit(current_user.id, educational_unit_id):
        raise HTTPException(403, "Só pode interagir com seu próprio polo")

    user_ip = request.client.host if request.client else "unknown"
    rows = await service.get_course_vacancies(
        course_id=course_id,
        educational_unit_id=educational_unit_id,
        requested_by_user_id=current_user.id,
        user_ip_address=user_ip,
    )
    xlsx = XlsxRenderService.render_to_base64(
        rows,
        sheet_name="Vagas por curso",
        column_labels=VACANCIES_COLUMNS,
        column_order=list(VACANCIES_COLUMNS.keys()),
    )

    return Response(
        content=base64.b64decode(xlsx),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="vagas_por_curso.xlsx"'},
    )

@router.get("/user/{user_id}/enrollments")
@limiter.limit("10/minute")
async def get_user_courses_pdf(
    request: Request,
    user_id: UUID,
    current_user: User = Depends(get_current_active_user),
    service: ReportService = Depends(get_report_service)
):
    """PDF listing a user's courses, components and classes"""
    if current_user.user_type_id == 5 and current_user.id != user_id:
        raise HTTPException(403, "Não autorizado")

    try:
        base64_pdf = await service.render_user_courses_pdf(user_id)

        return {"base64": base64_pdf, "mime_type": "application/pdf"}
    except ValueError as e:
        raise HTTPException(404, str(e))
