"""User course enrollment service - business logic for User Course entity"""
from typing import Any, List, Optional
from uuid import UUID

from src.application.logging.application_logger import ApplicationLogger
from src.application.mappers.user_course_mapper import UserCourseMapper
from src.data.models.course_model import CourseModel
from src.data.models.enrollment_waiting_list_model import EnrollmentWaitingListModel
from src.data.models.user_course_model import UserCourseModel
from src.data.repositories.course_repository import CourseRepository
from src.data.repositories.enrollment_waiting_list_repository import EnrollmentWaitingListRepository
from src.data.repositories.user_course_repository import UserCourseRepository
from src.application.services.base_service import BaseService
from src.domain.schemas.user_course import UserCourse, UserCourseBulkCreate, UserCourseCreate
from src.infrastructure.configuration.settings import settings
from src.infrastructure.handlers.datetime_handler import DateTimeHandler

class UserCourseService(BaseService):
    """Service for User Course enrollment business logic"""
    
    def __init__(
        self,
        repository: UserCourseRepository,
        course_repo: CourseRepository,
        waiting_list_repo: EnrollmentWaitingListRepository
    ):
        super().__init__(repository, 'user_course', mapper_class=UserCourseMapper)
        self.repository = repository
        self.course_repo = course_repo
        self.waiting_list_repo = waiting_list_repo
    
    async def enroll_user(
        self,
        dto: UserCourseCreate,
        enrolled_by_user_id: Optional[UUID] = None,
        user_ip_address: Optional[str] = None
    ) -> UserCourse:
        """Enroll a user in a course with validation"""
        saved_model: UserCourseModel
        
        try:
            user_id: UUID = dto.user_id
            course_id: UUID = dto.course_id
            # Validate if enrolling is allowed in the current month
            currentMonth: int = DateTimeHandler.now().date().month

            if currentMonth not in settings.ENROLLMENT_MONTHS:
                raise PermissionError('O período de matrículas já se encerrou')
            
            # Check if already enrolled
            existingEnrollment: UserCourseModel | None = await self.repository.get_by_user_and_course(user_id, course_id)

            if existingEnrollment:
                if existingEnrollment.active:
                    raise ValueError("Usuário já matriculado")
                else:
                    # Reactivate enrollment
                    existingEnrollment.active = True
                    saved_model = await self.repository.update(existingEnrollment)
                    self.repository.session.commit()

                    return UserCourseMapper.model_to_schema(saved_model)
            
            # Validate enrollment rules
            await self._validate_enrollment_rules(user_id, course_id)
            # Check if course has available seats
            course: CourseModel | None = await self.course_repo.get_by_id(course_id)
            enrollments: List[UserCourseModel] = await self.repository.get_active_by_course_id(course_id)

            if len(enrollments) >= course.total_seat_limit:
                return await self._add_to_waiting_list(user_id, course_id)

            # Create new enrollment
            create_model: UserCourseModel = UserCourseMapper.create_to_model(dto)
            saved_model: UserCourseModel = await self.repository.create(create_model)

            # Log creation
            if enrolled_by_user_id:
                from src.data.repositories.log_student_enrollment_repository import LogStudentEnrollmentRepository
                log_repo = LogStudentEnrollmentRepository(self.repository.session)
                await log_repo.log(
                    enrolled=True,
                    user_id=enrolled_by_user_id,
                    user_ip_address=user_ip_address or "unknown",
                    course_id=course_id
                )
            
            self.repository.session.commit()
            
            return UserCourseMapper.model_to_schema(saved_model)
        except Exception as e:
            await ApplicationLogger.log_error(e, reraise=True)

    async def bulk_enroll(self, dto: UserCourseBulkCreate) -> dict[str, Any]:
        """Bulk enroll users after validation"""
        try:
            validation: dict[str, Any] = await self._validate_bulk_enrollment(UUID(dto.course_id), dto.user_ids)
            
            if not validation['valid']:
                return {
                    'success': False,
                    'course_id': dto.course_id,
                    'validation': validation,
                    'enrolled': []
                }
            
            enrolled: List[UserCourse] = []

            for user_id in dto.user_ids:
                enroll_dto: UserCourseCreate = UserCourseCreate(user_id=user_id, course_id=dto.course_id)
                result: UserCourse = await self.enroll_user(enroll_dto)
                enrolled.append(result)
            
            self.repository.session.commit()
            enrolled_count: int = len(enrolled)
            
            return {
                'success': True,
                'course_id': dto.course_id,
                'enrolled_count': enrolled_count,
                'available_seats_remaining': validation['available_seats'] - enrolled_count,
                'enrolled': enrolled
            }
        except Exception as e:
            await ApplicationLogger.log_error(e, reraise=True)
    
    async def unenroll_user(
        self,
        enrollment_id: UUID,
        unenrolled_by_user_id: Optional[UUID] = None,
        user_ip_address: Optional[str] = None
    ) -> bool:
        """Unenroll a user from a course"""
        try:
            enrollment: UserCourseModel | None = await self.repository.get_by_id(enrollment_id)

            if not enrollment:
                raise ValueError("Enrollment not found")
            
            course_id: UUID = enrollment.course_id
            
            if not enrollment.active:
                raise ValueError("Enrollment already inactive")
            
            unenrolled: bool = await self.repository.deactivate_enrollment(enrollment_id)
            
            if unenrolled:
                # Enroll next user from waiting list
                await self._enroll_next_from_waiting_list(course_id)

            # Log unenrollment
            if unenrolled_by_user_id:
                from src.data.repositories.log_student_enrollment_repository import LogStudentEnrollmentRepository
                log_repo = LogStudentEnrollmentRepository(self.repository.session)
                await log_repo.log(
                    enrolled=False,
                    user_id=unenrolled_by_user_id,
                    user_ip_address=user_ip_address or "unknown",
                    course_id=course_id
                )

            self.repository.session.commit()
            
            return unenrolled
        except Exception as e:
            await ApplicationLogger.log_error(e, reraise=True)
    
    async def get_user_enrollments(self, user_id: UUID) -> List[UserCourse]:
        """Get all enrollments for a user"""
        try:
            models = await self.repository.get_by_user_id(user_id)

            return [UserCourseMapper.model_to_schema(model) for model in models]
        except Exception as e:
            await ApplicationLogger.log_error(e, reraise=True)
    
    async def get_user_active_enrollments_with_details(self, user_id: UUID) -> List[dict[str, Any]]:
        """Get user's active enrollments with course and shift details"""
        try:
            enrollments_with_details: List[dict[str, Any]] = []
            active_enrollments: List[UserCourseModel] = await self.repository.get_active_by_user_id(user_id)

            for enrollment in active_enrollments:
                course: CourseModel | None = await self.course_repo.get_by_id(enrollment.course_id)

                if course:
                    enrollments_with_details.append({
                        'enrollment_id': enrollment.id,
                        'course_id': course.id,
                        'shift_type_id': course.shift_type_id,
                        'enrolled_at': enrollment.created_at
                    })
            
            return enrollments_with_details
        except Exception as e:
            await ApplicationLogger.log_error(e, reraise=True)
    
    async def get_active_course_enrollments(self, course_id: UUID) -> List[UserCourse]:
        """Get active enrollments for a course"""
        try:
            models: List[UserCourseModel] = await self.repository.get_active_by_course_id(course_id)
            
            return [UserCourseMapper.model_to_schema(model) for model in models]
        except Exception as e:
            await ApplicationLogger.log_error(e, reraise=True)
    
    async def get_enrollment_summary(self, user_id: UUID) -> dict[str, Any]:
        """Get enrollment summary for a user"""
        try:
            
            active_enrollments: List[dict[str, Any]] = await self.get_user_active_enrollments_with_details(user_id)
            shifts_enrolled: set = set()

            for enrollment in active_enrollments:
                shifts_enrolled.add(enrollment['shift_type_id'])
            
            shift_names: dict[int, str] = {1: "Manhã", 2: "Tarde", 3: "Noite"}
            enrolled_shifts: List[str] = [shift_names.get(s, f"shift_{s}") for s in shifts_enrolled]
            
            return {
                'user_id': user_id,
                'total_enrollments': len(active_enrollments),
                'max_enrollments': self._get_maximum_enrollments_count(),
                'remaining_slots': self._get_maximum_enrollments_count() - len(active_enrollments),
                'enrolled_shifts': enrolled_shifts,
                'available_shifts': [s for s in shift_names.values() if s not in enrolled_shifts],
                'enrollments': active_enrollments
            }
        except Exception as e:
            await ApplicationLogger.log_error(e, reraise=True)

    # Private methods
    @staticmethod
    def _get_maximum_enrollments_count() -> int:
        MAX_ENROLLMENTS_COUNT: int = 3

        return MAX_ENROLLMENTS_COUNT

    async def _validate_bulk_enrollment(self, course_id: UUID, user_ids: List[str]) -> dict[str, Any]:
        """
        Validate if users can be enrolled in a course.
        Returns validation result with available seats and any issues.
        """
        try:
            course: CourseModel | None = await self.course_repo.get_by_id(course_id)

            if not course:
                return {'valid': False, 'reason': 'Curso não encontrado'}
            
            if not course.active:
                return {'valid': False, 'reason': 'Curso inativo'}
            
            enrollments: List[UserCourseModel] = await self.repository.get_active_by_course_id(course_id)
            available_seats: int = course.total_seat_limit - len(enrollments)
            requested: int = len(user_ids)
            
            if requested > available_seats:
                return {
                    'course_id': course_id,
                    'valid': False,
                    'reason': f'Insufficient seats',
                    'available_seats': available_seats,
                    'requested': requested
                }
            
            # Check each user
            troubledEnrollments: List[dict[str, str]] = []

            for user_id in user_ids:
                try:
                    user_uuid: UUID = UUID(user_id)
                    existing: UserCourseModel | None = await self.repository.get_by_user_and_course(user_uuid, course_id)

                    if existing and existing.active:
                        troubledEnrollments.append({'user_id': user_id, 'issue': 'Already enrolled'})
                        continue
                    
                    try:
                        await self._validate_enrollment_rules(user_uuid, course_id)
                    except ValueError as e:
                        troubledEnrollments.append({'user_id': user_id, 'issue': str(e)})
                except ValueError:
                    troubledEnrollments.append({'user_id': user_id, 'issue': 'Invalid user ID format'})

            self.repository.session.commit()
            
            return {
                'course_id': course_id,
                'valid': len(troubledEnrollments) == 0,
                'available_seats': available_seats,
                'requested': requested,
                'valid_enrollments': requested - len(troubledEnrollments),
                'issues': troubledEnrollments
            }
        except Exception as e:
            await ApplicationLogger.log_error(e, reraise=True)
    
    async def _validate_enrollment_rules(self, user_id: UUID, new_course_id: UUID) -> None:
        """
        Validate enrollment business rules:
        1. Maximum 3 enrollments per user
        2. Cannot enroll in multiple courses with the same shift
        """
        try:
            # Get user's active enrollments
            active_enrollments: List[UserCourseModel] = await self.repository.get_active_by_user_id(user_id)
            
            # Maximum 3 of enrollments
            if len(active_enrollments) >= self._get_maximum_enrollments_count():
                raise ValueError(f"Aluno já está com o limite de {self._get_maximum_enrollments_count()} matrículas ativas")
            
            for active_enrollment in active_enrollments:
                active_course: CourseModel | None = await self.course_repo.get_by_id(active_enrollment.course_id)
                new_course: CourseModel | None = await self.course_repo.get_by_id(new_course_id)

                if new_course.name == active_course.name:
                    raise ValueError("Aluno já tem matricula para este curso em outro turno")

        except Exception as e:
            await ApplicationLogger.log_error(e, reraise=True)

    async def _add_to_waiting_list(self, user_id: UUID, course_id: UUID) -> dict[str, Any]:
        """Add user to the waiting list for a full course."""
        # Check if already on list
        existing: EnrollmentWaitingListModel | None = await self.waiting_list_repo.get_by_user_and_course(user_id, course_id)

        if existing:
            raise ValueError("Já na lista de espera")
        
        last_position: int = await self.waiting_list_repo.get_last_position(course_id)
        
        from uuid import uuid4
        
        model = EnrollmentWaitingListModel(
            id=uuid4(),
            created_at=DateTimeHandler.now(),
            user_id=user_id,
            course_id=course_id,
            position=last_position + 1
        )
        saved_model: EnrollmentWaitingListModel = await self.waiting_list_repo.create(model)
        
        return {
            "message": "Limite de matrículas já atingido. Você está na lista de espera.",
            "position": last_position + 1,
            "waiting_list_id": saved_model.id
        }
    
    async def _enroll_next_from_waiting_list(self, course_id: UUID) -> None:
        """Enroll the next user from the waiting list."""
        next_in_line: EnrollmentWaitingListModel | None = await self.waiting_list_repo.get_next_in_line(course_id)
        
        if next_in_line:
            user_id: UUID = next_in_line.user_id
            
            # Remove from waiting list
            await self.waiting_list_repo.remove_user(user_id, course_id)
            
            # Enroll
            dto = UserCourseCreate(user_id=str(user_id), course_id=str(course_id))
            await self.enroll_user(dto)
