"""Class attendance controller"""
from datetime import date
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from src.application.services.class_attendance_service import ClassAttendanceService
from src.data.repositories.class_attendance_repository import ClassAttendanceRepository
from src.data.repositories.document_repository import DocumentRepository
from src.data.repositories.student_absence_justification_repository import StudentAbsenceJustificationRepository
from src.data.repositories.user_course_repository import UserCourseRepository
from src.data.repositories.class_repository import ClassRepository
from src.data.repositories.course_component_repository import CourseComponentRepository
from src.data.db_context.database import get_db
from src.api.dependencies.auth_dependencies import get_current_active_user
from src.domain.schemas.class_attendance import BulkAttendanceCreate
from src.domain.schemas.document import DocumentCreate
from src.domain.schemas.user import User

router = APIRouter(
    prefix="/attendance",
    tags=["Attendance"],
    dependencies=[Depends(get_current_active_user)]
)

def get_attendance_service(db: Session = Depends(get_db)) -> ClassAttendanceService:
    repository = ClassAttendanceRepository(db)
    user_course_repo = UserCourseRepository(db)
    class_repo = ClassRepository(db)
    component_repo = CourseComponentRepository(db)
    document_repo = DocumentRepository(db)
    absence_justification_repo = StudentAbsenceJustificationRepository(db)

    return ClassAttendanceService(
        repository,
        user_course_repo,
        class_repo,
        component_repo,
        document_repo,
        absence_justification_repo
    )

@router.post("/class/take")
async def take_attendance(
    dto: BulkAttendanceCreate,
    current_user: User = Depends(get_current_active_user),
    service: ClassAttendanceService = Depends(get_attendance_service)
):
    """Take attendance for a class. Educators (4) and Coordinators (3) only."""
    if current_user.user_type_id not in [3, 4]:
        raise HTTPException(status_code=403, detail="Não autorizado")
    
    try:
        return await service.take_attendance(dto)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/class/{class_id}")
async def get_class_attendance(
    class_id: UUID,
    current_user: User = Depends(get_current_active_user),
    service: ClassAttendanceService = Depends(get_attendance_service)
):
    """Take attendance for a class. Educators (4) and Coordinators (3) only."""
    if current_user.user_type_id not in [3, 4]:
        raise HTTPException(status_code=403, detail="Não autorizado")
    
    """Get attendance for a class."""
    return await service.get_class_attendance(class_id)

@router.get("/user/{user_id}/class/{class_id}")
async def get_user_class_attendance(
    user_id: UUID,
    class_id: UUID,
    current_user: User = Depends(get_current_active_user),
    service: ClassAttendanceService = Depends(get_attendance_service)
):
    """Get attendance summary for a user in a class."""
    if current_user.user_type_id not in [3, 4] and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Can only view your own attendance")
    
    return await service.get_user_class_attendance(user_id, class_id)


@router.get("/user/{user_id}/classes")
async def get_user_classes(
    user_id: UUID,
    date: Optional[date] = Query(None),
    attended: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    service: ClassAttendanceService = Depends(get_attendance_service)
):
    """Get all classes for a user with filters."""
    if current_user.user_type_id not in [3, 4] and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Can only view your own classes")
    
    return await service.get_user_classes(
        user_id=user_id,
        date=date,
        attended=attended,
        page=page,
        page_size=page_size
    )

@router.post("/{attendance_id}/justify")
async def submit_absence_justification(
    attendance_id: UUID,
    document: DocumentCreate,
    current_user: User = Depends(get_current_active_user),
    service: ClassAttendanceService = Depends(get_attendance_service)
):
    """
    Submit a justification document for an absence.
    """
    try:
        return await service.submit_absence_justification(attendance_id, document, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
