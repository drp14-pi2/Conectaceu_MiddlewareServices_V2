"""Class repository"""
from datetime import date
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import select, and_

from src.data.models.class_model import ClassModel
from src.data.repositories.base.base_repository import BaseRepository

class ClassRepository(BaseRepository[ClassModel]):
    """Repository for Class entity"""
    
    def __init__(self, session: Session):
        super().__init__(session, ClassModel)
    
    async def get_by_component_id(self, component_id: UUID) -> List[ClassModel]:
        """Get all classes for a component"""
        stmt = select(ClassModel).where(ClassModel.course_component_id == component_id)
        result = self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def get_by_component_and_month(self, component_id: UUID, month: int) -> List[ClassModel]:
        """Get all classes for a component in a specific month"""
        from sqlalchemy import extract
        
        stmt = select(ClassModel).where(
            and_(
                ClassModel.course_component_id == component_id,
                extract('month', ClassModel.date) == month
            )
        ).order_by(ClassModel.date)
        result = self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def get_active_by_component_id(self, component_id: UUID) -> List[ClassModel]:
        """Get all active classes for a component"""
        stmt = select(ClassModel).where(
            ClassModel.course_component_id == component_id,
            ClassModel.active == True
        )
        result = self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def find_by_filters(
        self,
        component_id: Optional[UUID] = None,
        active: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[ClassModel]:
        """Find classes with filters"""
        conditions = []
        
        if component_id:
            conditions.append(ClassModel.course_component_id == component_id)
        if active is not None:
            conditions.append(ClassModel.active == active)
        
        stmt = select(ClassModel)
        if conditions:
            stmt = stmt.where(and_(*conditions))
        stmt = stmt.offset(skip).limit(limit)
        
        result = self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def class_exists(self, component_id: UUID
    ) -> bool:
        """Validates if classes exist for the given component and shift"""
        stmt = select(ClassModel).where(
            ClassModel.course_component_id == component_id
            and ClassModel.active
        )
        classes = self.session.execute(stmt)
        return classes.scalar_one_or_none() is not None
    
    async def increment_seats(self, class_id: UUID) -> bool:
        """Increment seats in use"""
        class_ = await self.get_by_id(class_id)
        if class_:
            class_.seats_in_use += 1
            self.session.flush()
            return True
        return False
    
    async def decrement_seats(self, class_id: UUID) -> bool:
        """Decrement seats in use"""
        class_ = await self.get_by_id(class_id)
        if class_ and class_.seats_in_use > 0:
            class_.seats_in_use -= 1
            self.session.flush()
            return True
        return False
    
    async def deactivate(self, class_id: UUID) -> bool:
        """Deactivate class"""
        class_ = await self.get_by_id(class_id)
        if class_:
            class_.active = False
            self.session.flush()
            return True
        return False
    
    async def activate(self, class_id: UUID) -> bool:
        """Deactivate class"""
        class_ = await self.get_by_id(class_id)
        if class_:
            class_.active = True
            self.session.flush()
            return True
        return False
    
    async def get_by_date_and_component(self, component_id: UUID, date: date) -> Optional[ClassModel]:
        """Check if a class exists for a component on a specific date"""
        from datetime import datetime as dt
        start = dt.combine(date, dt.min.time())
        end = dt.combine(date, dt.max.time())
        
        stmt = select(ClassModel).where(
            and_(
                ClassModel.course_component_id == component_id,
                ClassModel.date >= start,
                ClassModel.date <= end
            )
        )
        result = self.session.execute(stmt)
        return result.scalar_one_or_none()
