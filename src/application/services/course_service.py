"""Course service - business logic for Course entity"""
from typing import Optional
from uuid import UUID

from src.application.logging.application_logger import ApplicationLogger
from src.data.repositories.course_repository import CourseRepository
from src.data.repositories.course_component_repository import CourseComponentRepository
from src.application.services.base_service import BaseService
from src.application.mappers.dto_to_entity_mapper import DtoToEntityMapper
from src.application.mappers.entity_to_model_mapper import EntityToModelMapper
from src.application.mappers.model_to_entity_mapper import ModelToEntityMapper
from src.application.mappers.entity_to_view_model_mapper import EntityToViewModelMapper
from src.application.mappers.update_mapper import UpdateMapper
from src.domain.dtos.course_dto import CourseCreateDTO, CourseUpdateDTO
from src.domain.view_models.course_component_view_model import CourseComponentViewModel
from src.domain.view_models.course_view_model import CourseViewModel

class CourseService(BaseService):
    """Service for Course business logic"""
    
    def __init__(
        self, 
        repository: CourseRepository,
        component_repo: CourseComponentRepository
    ):
        super().__init__(repository, 'course', mapper_class=ModelToEntityMapper)
        self.repository = repository
        self.component_repo = component_repo
    
    async def create_course(
        self, 
        dto: CourseCreateDTO,
        created_by_user_id: Optional[UUID] = None,
        user_ip_address: Optional[str] = None
    ) -> CourseViewModel:
        """Create a new course"""
        try:
            # Check if name already exists
            existing = await self.repository.get_by_name(dto.name)
            if existing:
                raise ValueError("Nome de curso já existe")
            
            # Business rule: Validate workload
            if dto.workload < 1:
                raise ValueError("Carga horária deve ser de pelo menos 1 (uma) hora")
            
            # Convert DTO -> Entity
            entity = DtoToEntityMapper.course(dto)
            
            # Convert Entity -> Model and save
            model = EntityToModelMapper.course(entity)
            saved_model = await self.repository.create(model)

            if created_by_user_id:
                from src.data.repositories.log_course_creation_repository import LogCourseCreationRepository
                
                log_repo = LogCourseCreationRepository(self.repository.session)
                await log_repo.log(
                    name=saved_model.name,
                    total_seat_limit=saved_model.total_seat_limit,
                    workload=saved_model.workload,
                    active=saved_model.active,
                    user_ip_address=user_ip_address or "unknown",
                    user_id=created_by_user_id.bytes
                )
            
            self.repository.session.commit()

            # Convert back to ViewModel
            saved_entity = ModelToEntityMapper.course(saved_model)
            saved_couse_viewmodel = EntityToViewModelMapper.course(saved_entity)

            return saved_couse_viewmodel
        except Exception as e:
            await ApplicationLogger.log_error(e, reraise=True)
    
    async def update_course(self, course_id: UUID, dto: CourseUpdateDTO) -> CourseViewModel:
        """Update course with validation"""
        try:
            model = await self.repository.get_by_id(course_id)
            if not model:
                raise ValueError("Curso não encontrado")
            
            # Check name uniqueness if being updated
            if dto.name:
                existing = await self.repository.get_by_name(dto.name)
                if existing and existing.id != model.id:
                    raise ValueError("Nome de curso já existe")
            
            # Convert to entity and apply updates
            entity = ModelToEntityMapper.course(model)
            updated_entity = UpdateMapper.course(entity, dto)
            
            # Save changes
            updated_model = EntityToModelMapper.course(updated_entity)
            saved_model = await self.repository.update(updated_model)

            self.repository.session.commit()
            
            saved_entity = ModelToEntityMapper.course(saved_model)
            return EntityToViewModelMapper.course(saved_entity)
        except Exception as e:
            await ApplicationLogger.log_error(e, reraise=True)
    
    async def deactivate_course(self, course_id: UUID) -> dict:
        """Deactivate a course, its components, and classes"""
        try:
            course = await self.repository.get_by_id(course_id)
            if not course:
                raise ValueError("Curso não encontrado")
            
            if not course.active:
                raise ValueError("Curso já está desativado")
            
            # Get all components for this course
            components = await self.component_repo.get_by_course_id(course_id)
            
            deactivated_count = 0
            for component in components:
                if component.active:
                    await self.component_repo.deactivate(UUID(bytes=component.id))
                    deactivated_count += 1
            
            # Deactivate the course
            await self.repository.deactivate(course_id)

            self.repository.session.commit()
            
            return {
                "success": True,
                "course_id": course_id,
                "deactivated_components": deactivated_count
            }
        except Exception as e:
            await ApplicationLogger.log_error(e, reraise=True)
    
    async def activate_course(self, course_id: UUID) -> dict:
        """Activate a course"""
        try:
            course = await self.repository.get_by_id(course_id)
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
    ) -> list[CourseViewModel]:
        """Find courses with filters"""
        try:
            skip = (page - 1) * page_size
            
            models = await self.repository.find_by_filters(
                name=name,
                active=active,
                educator_id=educator_id,
                skip=skip,
                limit=page_size
            )
            
            total = await self.repository.count({'active': active})
            
            entities = [ModelToEntityMapper.course(model) for model in models]
            view_models = [EntityToViewModelMapper.course(entity) for entity in entities]
            
            return view_models
        except Exception as e:
            await ApplicationLogger.log_error(e, reraise=True)
    
    async def get_course_with_components(self, course_id: UUID) -> CourseViewModel:
        """Get course with its components"""
        try:
            course_model = await self.repository.get_by_id(course_id)
            if not course_model:
                raise ValueError("Course not found")
            
            components = await self.component_repo.get_by_course_id(course_id)
            
            course_entity = ModelToEntityMapper.course(course_model)
            component_entities = [ModelToEntityMapper.course_component(c) for c in components]
            course_viewmodel = EntityToViewModelMapper.course(course_entity)
            course_viewmodel.course_components = [EntityToViewModelMapper.course_component(c) for c in component_entities]
            
            return course_viewmodel
        except Exception as e:
            await ApplicationLogger.log_error(e, reraise=True)