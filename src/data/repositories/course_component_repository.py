"""Course component repository"""
from typing import List
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import select

from src.data.models.course_component_model import CourseComponentModel
from src.data.repositories.base.base_repository import BaseRepository

class CourseComponentRepository(BaseRepository[CourseComponentModel]):
    """Repository for Course Component entity"""
    
    def __init__(self, session: Session):
        super().__init__(session, CourseComponentModel)
    
    async def get_by_course_id(self, course_id: UUID) -> List[CourseComponentModel]:
        """Get all components for a course"""
        stmt = select(CourseComponentModel).where(
            CourseComponentModel.course_id == course_id
        )
        result = self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def get_active_by_course_id(self, course_id: UUID) -> List[CourseComponentModel]:
        """Get all active components for a course"""
        stmt = select(CourseComponentModel).where(
            CourseComponentModel.course_id == course_id,
            CourseComponentModel.active == True
        )
        result = self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def component_exists(self, name: str, course_id: UUID) -> bool:
        """Get component by exact name"""
        from sqlalchemy import and_
        conditions = [CourseComponentModel.name == name]
        conditions.append(CourseComponentModel.course_id == course_id)
        stmt = select(CourseComponentModel).where(and_(*conditions))
        result = self.session.execute(stmt)
        return result.scalar_one_or_none() is not None
    
    async def deactivate(self, component_id: UUID) -> bool:
        """Deactivate component"""
        component = await self.get_by_id(component_id)
        if component:
            component.active = False
            self.session.flush()
            return True
        return False
    
    async def activate(self, component_id: UUID) -> bool:
        """Activate component"""
        component = await self.get_by_id(component_id)
        if component:
            component.active = True
            self.session.flush()
            return True
        return False
