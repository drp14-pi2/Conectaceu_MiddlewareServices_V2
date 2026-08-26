"""Class service - business logic for Class entity"""
from datetime import date, datetime
from typing import List
from uuid import UUID, uuid4

from src.application.logging.application_logger import ApplicationLogger
from src.data.repositories.class_repository import ClassRepository
from src.data.repositories.course_component_repository import CourseComponentRepository
from src.data.repositories.course_repository import CourseRepository
from src.data.repositories.user_course_repository import UserCourseRepository
from src.application.services.base_service import BaseService
from src.application.mappers.dto_to_entity_mapper import DtoToEntityMapper
from src.application.mappers.entity_to_model_mapper import EntityToModelMapper
from src.application.mappers.model_to_entity_mapper import ModelToEntityMapper
from src.application.mappers.entity_to_view_model_mapper import EntityToViewModelMapper
from src.application.mappers.update_mapper import UpdateMapper
from src.domain.dtos.class_dto import ClassBulkCreateDTO, ClassCreateDTO, ClassUpdateDTO, ClassFilterDTO
from src.domain.entities.class_ import Class
from src.domain.view_models.class_view_model import ClassViewModel
from src.infrastructure.handlers.datetime_handler import DateTimeHandler

class ClassService(BaseService):
    """Service for Class business logic"""
    
    def __init__(
        self,
        repository: ClassRepository,
        component_repo: CourseComponentRepository,
        user_course_repo: UserCourseRepository,
        course_repo: CourseRepository
    ):
        super().__init__(repository, 'class_', mapper_class=ModelToEntityMapper)
        self.repository = repository
        self.component_repo = component_repo
        self.user_course_repo = user_course_repo
        self.course_repo = course_repo
    
    async def create_class(self, dto: ClassCreateDTO) -> ClassViewModel:
        """Create a new class"""
        try:
            # Validate component exists and is active
            component = await self.component_repo.get_by_id(UUID(dto.component_id))
            if not component:
                raise ValueError("Component not found")
            if not component.active:
                raise ValueError("Component is not active")
            
            entity = DtoToEntityMapper.class_(dto)
            model = EntityToModelMapper.class_(entity)
            saved_model = await self.repository.create(model)
            self.repository.session.commit()
            saved_entity = ModelToEntityMapper.class_(saved_model)
            return EntityToViewModelMapper.class_(saved_entity)
        except Exception as e:
            await ApplicationLogger.log_error(e, reraise=True)
    
    async def bulk_create_classes(self, dto: ClassBulkCreateDTO) -> dict:
        """Create one class per date in the range"""
        component = await self.component_repo.get_by_id(UUID(dto.course_component_id))
        if not component:
            raise ValueError("Componente não encontrado")
        
        dates = self._generate_class_dates(dto.start_date, dto.end_date, dto.days_of_week)
        
        if not dates:
            raise ValueError("Nenhuma data encontrada no período e dias selecionados")
        
        created = []
        skipped = []
        
        for class_date in dates:
            # Check if class already exists for this component and date
            existing = await self.repository.get_by_date_and_component(
                component_id=UUID(dto.course_component_id),
                date=class_date
            )
            if existing:
                skipped.append(class_date.isoformat())
                continue
            
            entity = Class(
                id=uuid4(),
                created_at=DateTimeHandler.now(),
                updated_at=None,
                seats_in_use=0,
                active=True,
                date=datetime.combine(class_date, datetime.min.time()),
                course_component_id=UUID(dto.course_component_id)
            )
            model = EntityToModelMapper.class_(entity)
            await self.repository.create(model)
            created.append(class_date.isoformat())
        
        self.repository.session.commit()
        
        return {
            'component_id': dto.course_component_id,
            'total_dates': len(dates),
            'created': len(created),
            'skipped': len(skipped),
            'created_dates': created,
            'skipped_dates': skipped
        }
    
    async def update_class(self, class_id: UUID, dto: ClassUpdateDTO) -> ClassViewModel:
        """Update a class"""
        try:
            model = await self.repository.get_by_id(class_id)
            if not model:
                raise ValueError("Class not found")
            
            entity = ModelToEntityMapper.class_(model)
            updated_entity = UpdateMapper.class_(entity, dto)
            updated_model = EntityToModelMapper.class_(updated_entity)
            saved_model = await self.repository.update(updated_model)
            self.repository.session.commit()
            saved_entity = ModelToEntityMapper.class_(saved_model)
            return EntityToViewModelMapper.class_(saved_entity)
        except Exception as e:
            await ApplicationLogger.log_error(e, reraise=True)
    
    async def find_classes(self, filters: ClassFilterDTO) -> list[ClassViewModel]:
        """Find classes with filters"""
        try:
            skip = (filters.page - 1) * filters.page_size
            
            models = await self.repository.find_by_filters(
                component_id=UUID(filters.component_id) if filters.component_id else None,
                active=filters.active,
                skip=skip,
                limit=filters.page_size
            )
            
            entities = [ModelToEntityMapper.class_(model) for model in models]
            view_models = [EntityToViewModelMapper.class_(entity) for entity in entities]
            
            return view_models
        except Exception as e:
            await ApplicationLogger.log_error(e, reraise=True)
    
    async def deactivate_class(self, course_id: UUID) -> bool:
        """Deactivate a class and all its active enrollments"""
        try:
            class_ = await self.repository.get_by_id(course_id)
            if not class_:
                raise ValueError("Class not found")
            
            if not class_.active:
                raise ValueError("Class already deactivated")
            
            # Get all active enrollments for this class
            active_enrollments = await self.user_course_repo.get_active_by_course_id(course_id)
            
            # Deactivate all enrollments and log the action
            for enrollment in active_enrollments:
                enrollment.active = False
                await self.user_course_repo.update(enrollment)
            
            # Deactivate the class
            result = await self.repository.deactivate(course_id)
            self.repository.session.commit()
            
            # Return summary
            return {
                'success': result,
                'class_id': course_id,
                'unenrolled_students': len(active_enrollments)
            }
        except Exception as e:
            await ApplicationLogger.log_error(e, reraise=True)
    
    async def activate_class(self, class_id: UUID) -> bool:
        """Activate a class"""
        try:
            class_ = await self.repository.get_by_id(class_id)
            if not class_:
                raise ValueError("Class not found")
            
            if class_.active:
                raise ValueError("Class already active")
            
            # Check if component is active
            component = await self.component_repo.get_by_id(UUID(bytes=class_.course_component_id))
            if not component or not component.active:
                raise ValueError("Cannot activate class because component is inactive")
            
            result = await self.repository.activate(class_id)
            self.repository.session.commit()
            
            return result
        except Exception as e:
            await ApplicationLogger.log_error(e, reraise=True)
    
    async def get_available_seats(self, class_id: UUID) -> dict:
        """Get available seats for a class"""
        try:
            class_ = await self.repository.get_by_id(class_id)
            if not class_:
                raise ValueError("Class not found")
            
            component = await self.component_repo.get_by_id(UUID(bytes=class_.course_component_id))
            
            return {
                'class_id': class_id,
                'seats_in_use': class_.seats_in_use,
                'seat_limit': component.seat_limit_per_class if component else 0,
                'available_seats': component.seat_limit_per_class - class_.seats_in_use if component else 0
            }
        except Exception as e:
            await ApplicationLogger.log_error(e, reraise=True)

    def _generate_class_dates(
        self,
        start_date: date,
        end_date: date,
        days_of_week: List[int]
    ) -> List[date]:
        """
        Generate class dates within a range for specific days of week.
        
        Args:
            start_date: Start of date range
            end_date: End of date range
            days_of_week: List of days (0=Monday, 6=Sunday)
        
        Returns:
            List of dates that match the criteria
        """
        from datetime import timedelta
        
        class_dates = []
        current_date = start_date
        
        while current_date <= end_date:
            if current_date.weekday() in days_of_week:
                class_dates.append(current_date)
            current_date += timedelta(days=1)
        
        return class_dates