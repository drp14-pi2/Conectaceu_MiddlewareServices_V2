"""Course service - business logic for Course entity"""
from typing import Any, List, Optional
from uuid import UUID

from src.application.logging.application_logger import ApplicationLogger
from src.data.models.course_component_model import CourseComponentModel
from src.data.models.course_model import CourseModel
from src.data.repositories.course_repository import CourseRepository
from src.data.repositories.course_component_repository import CourseComponentRepository
from src.application.services.base_service import BaseService
from src.application.mappers.course_mapper import CourseMapper
from src.domain.schemas.course import Course, CourseCreate, CourseList, CourseUpdate

class CourseService(BaseService):
    """Service for Course business logic"""
    
    def __init__(
        self, 
        repository: CourseRepository,
        component_repo: CourseComponentRepository
    ):
        super().__init__(repository, 'course', mapper_class=CourseMapper)
        self.repository = repository
        self.component_repo = component_repo
    
    async def create_course(
        self, 
        dto: CourseCreate,
        created_by_user_id: Optional[UUID] = None,
        user_ip_address: Optional[str] = None
    ) -> Course:
        """Create a new course"""
        try:
            # Check if name already exists
            existing_course: CourseModel | None = await self.repository.get_by_name(dto.name)

            if existing_course:
                raise ValueError("Nome de curso já existe")
            
            # Validate workload
            if dto.workload < 1:
                raise ValueError("Carga horária deve ser de pelo menos 1 (uma) hora")
            
            model: CourseModel = CourseMapper.create_to_model(dto)
            saved_model: CourseModel = await self.repository.create(model)

            if created_by_user_id:
                from src.data.repositories.log_course_creation_repository import LogCourseCreationRepository
                
                log_repo: LogCourseCreationRepository = LogCourseCreationRepository(self.repository.session)
                await log_repo.log(
                    name=saved_model.name,
                    total_seat_limit=saved_model.total_seat_limit,
                    workload=saved_model.workload,
                    active=saved_model.active,
                    user_ip_address=user_ip_address or "unknown",
                    user_id=created_by_user_id.bytes
                )
            
            self.repository.session.commit()

            return CourseMapper.model_to_schema(saved_model)
        except Exception as e:
            await ApplicationLogger.log_error(e, reraise=True)
    
    async def update_course(self, course_id: UUID, dto: CourseUpdate) -> Course:
        """Update course with validation"""
        try:
            model: CourseModel | None = await self.repository.get_by_id(course_id)

            if not model:
                raise ValueError("Curso não encontrado")
            
            if dto.name:
                existing: CourseModel | None = await self.repository.get_by_name(dto.name)

                if existing:
                    raise ValueError("Nome de curso já existe")
            
            updated_model: CourseModel = CourseMapper.update_model(model, dto)
            saved_model: CourseModel = await self.repository.update(updated_model)
            self.repository.session.commit()

            return CourseMapper.model_to_schema(saved_model)
        except Exception as e:
            await ApplicationLogger.log_error(e, reraise=True)
    
    async def deactivate_course(self, course_id: UUID) -> dict[str, Any]:
        """Deactivate a course, its components, and classes"""
        try:
            course: CourseModel | None = await self.repository.get_by_id(course_id)

            if not course:
                raise ValueError("Curso não encontrado")
            
            if not course.active:
                raise ValueError("Curso já está desativado")
            
            # Get all components for this course
            components: List[CourseComponentModel] = await self.component_repo.get_by_course_id(course_id)
            deactivated_components_count: int = 0

            for component in components:
                if component.active:
                    await self.component_repo.deactivate(UUID(bytes=component.id))
                    deactivated_components_count += 1
            
            # Deactivate the course
            await self.repository.deactivate(course_id)
            self.repository.session.commit()
            
            return {
                "success": True,
                "course_id": course_id,
                "deactivated_components": deactivated_components_count
            }
        except Exception as e:
            await ApplicationLogger.log_error(e, reraise=True)
    
    async def activate_course(self, course_id: UUID) -> dict[str, Any]:
        """Activate a course"""
        try:
            course: CourseModel | None = await self.repository.get_by_id(course_id)

            if not course:
                raise ValueError("Curso não encontrado")
            
            if course.active:
                raise ValueError("Curso já está ativado")
            
            await self.repository.activate(course_id)
            self.repository.session.commit()
            
            return {
                "success": True,
                "course_id": course_id,
                "message": "Curso ativado com sucesso"
            }
        except Exception as e:
            await ApplicationLogger.log_error(e, reraise=True)
    
    async def find_courses(
        self,
        name: Optional[str] = None,
        active: Optional[bool] = None,
        educator_id: Optional[UUID] = None,
        page: int = 1,
        page_size: int = 10
    ) -> List[Course]:
        """Find courses with filters"""
        try:
            skip: int = (page - 1) * page_size
            models: List[CourseModel] = await self.repository.find_by_filters(
                name=name,
                active=active,
                educator_id=educator_id,
                skip=skip,
                limit=page_size
            )
            
            return [CourseMapper.model_to_schema(model) for model in models]
        except Exception as e:
            await ApplicationLogger.log_error(e, reraise=True)
    
    async def get_course_with_components(self, course_id: UUID) -> CourseList:
        """Get course with its components"""
        try:
            course: CourseModel | None = await self.repository.get_by_id(course_id)

            if not course:
                raise ValueError("Course not found")

            from src.application.mappers.course_component_mapper import CourseComponentMapper

            components: List[CourseComponentModel] = await self.component_repo.get_by_course_id(course_id)
            result = CourseList(
                id=UUID(bytes=course.id),
                name=course.name,
                workload=course.workload,
                active=course.active,
                shift_type_id=course.shift_type_id,
                total_seat_limit=course.total_seat_limit,
                components=[CourseComponentMapper.model_to_schema(c) for c in components]
            )
            
            return result
        except Exception as e:
            await ApplicationLogger.log_error(e, reraise=True)
