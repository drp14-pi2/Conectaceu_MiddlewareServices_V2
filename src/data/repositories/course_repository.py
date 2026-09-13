"""Course repository"""
from typing import Optional, List
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import or_, select, and_

from src.data.models.course_model import CourseModel
from src.data.repositories.base.base_repository import BaseRepository

class CourseRepository(BaseRepository[CourseModel]):
    """Repository for Course entity"""
    
    def __init__(self, session: Session):
        super().__init__(session, CourseModel)
    
    async def get_by_name(self, name: str) -> Optional[CourseModel]:
        """Get course by exact name"""
        stmt = select(CourseModel).where(CourseModel.name == name)
        result = self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def find_by_filters(
        self,
        name: Optional[str] = None,
        active: Optional[bool] = None,
        educator_id: Optional[UUID] = None,
        shift_type_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[CourseModel]:
        conditions = []
        
        if name:
            conditions.append(CourseModel.name.contains(name))
        if active is not None:
            conditions.append(CourseModel.active == active)
        if educator_id:
            conditions.append(
                or_(
                    CourseModel.responsible_educator_1 == educator_id,
                    CourseModel.responsible_educator_2 == educator_id
                )
            )
        if shift_type_id is not None:
            conditions.append(CourseModel.shift_type_id == shift_type_id)
        
        stmt = select(CourseModel)
        if conditions:
            stmt = stmt.where(and_(*conditions))
        stmt = stmt.offset(skip).limit(limit)
        
        result = self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def deactivate(self, course_id: UUID) -> bool:
        """Deactivate course"""
        course = await self.get_by_id(course_id)
        if course:
            course.active = False
            self.session.flush()
            return True
        return False
    
    async def activate(self, course_id: UUID) -> bool:
        """Activate course"""
        course = await self.get_by_id(course_id)
        if course:
            course.active = True
            self.session.flush()
            return True
        return False
