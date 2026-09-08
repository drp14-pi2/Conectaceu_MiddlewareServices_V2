"""Course component service - business logic for Course Component entity"""
from typing import List
from uuid import UUID

from src.application.logging.application_logger import ApplicationLogger
from src.application.mappers.course_component_mapper import CourseComponentMapper
from src.data.models.course_component_model import CourseComponentModel
from src.data.models.course_model import CourseModel
from src.data.repositories.course_component_repository import CourseComponentRepository
from src.application.services.base_service import BaseService
from src.data.repositories.course_repository import CourseRepository
from src.domain.schemas.course_component import CourseComponent, CourseComponentCreate, CourseComponentUpdate

class CourseComponentService(BaseService):
    """Service for Course Component business logic"""
    
    def __init__(
        self,
        repository: CourseComponentRepository,
        course_repository: CourseRepository
    ):
        super().__init__(repository, 'course_component', mapper_class=CourseComponentMapper)
        self.course_repo = course_repository
        self.repository = repository
    
    async def create_component(self, dto: CourseComponentCreate) -> CourseComponent:
        """Create a new course component"""
        try:
            # Validate course
            course: CourseModel | None = await self.course_repo.get_by_id(dto.course_id)

            if not course:
                raise ValueError("Curso não encontrado")

            # Validate if component already exists
            component_exists = await self.repository.component_exists(dto.name, UUID(bytes=course.id))

            if component_exists:
                raise ValueError("Componente já existe para este curso")

            # Create component
            model = CourseComponentMapper.create_to_model(dto)

            if not model.active:
                model.active = True

            saved_model = await self.repository.create(model)
            self.repository.session.commit()

            return CourseComponentMapper.model_to_schema(saved_model)
        except Exception as e:
            await ApplicationLogger.log_error(e, reraise=True)
    
    async def update_component(self, component_id: UUID, dto: CourseComponentUpdate) -> CourseComponent:
        """Update a course component"""
        try:
            # Validate component
            component: CourseComponentModel | None = await self.repository.get_by_id(component_id)

            if not component:
                raise ValueError("Componente não encontrado")

            if dto.name:
                component_exists: bool = await self.repository.component_exists(dto.name, UUID(bytes=component.course_id))

                if component_exists:
                    raise ValueError("Componente já existe com esse nome")

            # Update component
            updated_model: CourseComponentModel = CourseComponentMapper.update_model(component, dto)
            saved_model: CourseComponentModel = await self.repository.update(updated_model)
            self.repository.session.commit()

            return CourseComponentMapper.model_to_schema(saved_model)
        except Exception as e:
            await ApplicationLogger.log_error(e, reraise=True)
    
    async def get_course_components(self, course_id: UUID) -> List[CourseComponent]:
        """Get all components for a course"""
        try:
            models = await self.repository.get_by_course_id(course_id)

            return [CourseComponentMapper.model_to_schema(model) for model in models]
        except Exception as e:
            await ApplicationLogger.log_error(e, reraise=True)
    
    async def deactivate_component(self, component_id: UUID) -> bool:
        """Deactivate a component"""
        try:
            component: CourseComponentModel | None = await self.repository.get_by_id(component_id)

            if not component:
                raise ValueError("Componente não encontrado")
            
            if not component.active:
                raise ValueError("Componente já desativado")
            
            deactivated: bool = await self.repository.deactivate(component_id)
            self.repository.session.commit()
            
            return deactivated
        except Exception as e:
            await ApplicationLogger.log_error(e, reraise=True)
    
    async def activate_component(self, component_id: UUID) -> bool:
        """Activate a component"""
        try:
            component: CourseComponentModel | None = await self.repository.get_by_id(component_id)

            if not component:
                raise ValueError("Componente não encontrado")
            
            if component.active:
                raise ValueError("Componente já ativo")
            
            activated: bool = await self.repository.activate(component_id)
            self.repository.session.commit()
            
            return activated
        except Exception as e:
            await ApplicationLogger.log_error(e, reraise=True)
