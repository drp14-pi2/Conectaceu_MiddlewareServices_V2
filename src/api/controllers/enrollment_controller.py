"""User course enrollment controller"""
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, Request, HTTPException, status
from sqlalchemy.orm import Session

from src.application.services.user_course_service import UserCourseService
from src.data.repositories.course_repository import CourseRepository
from src.data.repositories.enrollment_waiting_list_repository import EnrollmentWaitingListRepository
from src.data.repositories.user_course_repository import UserCourseRepository
from src.data.db_context.database import get_db
from src.api.dependencies.auth_dependencies import get_current_active_user
from src.domain.schemas.user import User
from src.domain.schemas.user_course import UserCourse, UserCourseBulkCreate, UserCourseCreate

router = APIRouter(
    prefix="/enrollment",
    tags=["Enrollment"],
    dependencies=[Depends(get_current_active_user)]
)

def get_user_course_service(db: Session = Depends(get_db)) -> UserCourseService:
    """Dependency injection for UserCourseService"""
    repository = UserCourseRepository(db)
    course_repo = CourseRepository(db)
    waiting_list_repo = EnrollmentWaitingListRepository(db)

    return UserCourseService(repository, course_repo, waiting_list_repo)

@router.post("/", response_model=UserCourse, status_code=status.HTTP_201_CREATED)
async def enroll_user(
    request: Request,
    dto: UserCourseCreate,
    current_user: User = Depends(get_current_active_user),
    service: UserCourseService = Depends(get_user_course_service)
):
    """Enroll a user in a class."""
    try:
        user_ip: str = request.client.host if request.client else "unknown"

        return await service.enroll_user(
            dto,
            enrolled_by_user_id=current_user.id,
            user_ip_address=user_ip
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/bulk")
async def bulk_enroll(
    dto: UserCourseBulkCreate,
    current_user: User = Depends(get_current_active_user),
    service: UserCourseService = Depends(get_user_course_service)
):
    """
    Bulk enroll users in a class.
    Admin (1), Secretary (2), Coordinator (3), Educator (4) only.
    """
    if current_user.user_type_id not in [1, 2, 3, 4]:
        raise HTTPException(status_code=403, detail="Não autorizado")
    
    return await service.bulk_enroll(dto)

@router.get("/user/{user_id}", response_model=list[UserCourse])
async def get_user_enrollments(
    user_id: UUID,
    current_user: User = Depends(get_current_active_user),
    service: UserCourseService = Depends(get_user_course_service)
):
    """
    Get all enrollments for a user.
    - Staff can view any user
    - Users can view their own
    """
    if current_user.user_type_id not in [1, 2, 3, 4] and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Não autorizado")
    
    return await service.get_user_enrollments(user_id)

@router.get("/user/{user_id}/summary")
async def get_enrollment_summary(
    user_id: UUID,
    current_user: User = Depends(get_current_active_user),
    service: UserCourseService = Depends(get_user_course_service)
):
    """
    Get enrollment summary for a user.
    - Staff can view any user
    - Users can view their own
    """
    if current_user.user_type_id not in [1, 2, 3, 4] and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Não autorizado")
    
    return await service.get_enrollment_summary(user_id)

@router.get("/course/{course_id}", response_model=List[UserCourse])
async def get_course_enrollments(
    course_id: UUID,
    current_user: User = Depends(get_current_active_user),
    service: UserCourseService = Depends(get_user_course_service)
):
    """
    Get all enrollments for a class.
    Admin (1), Secretary (2), Coordinator (3), Educator (4) only.
    """
    if current_user.user_type_id == 5:
        raise HTTPException(status_code=403, detail="Não autorizado")
    
    return await service.get_active_course_enrollments(course_id)

@router.patch("/{enrollment_id}/unenroll")
async def unenroll_user(
    request: Request,
    enrollment_id: UUID,
    current_user: User = Depends(get_current_active_user),
    service: UserCourseService = Depends(get_user_course_service)
):
    """Unenroll a user from a class."""
    try:
        user_ip: str = request.client.host if request.client else "unknown"
        result: bool = await service.unenroll_user(
            enrollment_id,
            unenrolled_by_user_id=current_user.id,
            user_ip_address=user_ip
        )

        return {"message": "Matrícula cancelada com sucesso", "success": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
