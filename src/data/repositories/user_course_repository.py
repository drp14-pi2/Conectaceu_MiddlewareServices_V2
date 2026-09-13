"""User course enrollment repository"""
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import func, select

from src.data.models.user_course_model import UserCourseModel
from src.data.repositories.base.base_repository import BaseRepository

class UserCourseRepository(BaseRepository[UserCourseModel]):
    """Repository for User Course enrollment entity"""
    
    def __init__(self, session: Session):
        super().__init__(session, UserCourseModel)
    
    async def get_by_user_id(self, user_id: UUID) -> List[UserCourseModel]:
        """Get all enrollments for a user"""
        stmt = select(UserCourseModel).where(UserCourseModel.user_id == user_id)
        result = self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def get_active_by_user_id(self, user_id: UUID) -> List[UserCourseModel]:
        """Get active enrollments for a user"""
        stmt = select(UserCourseModel).where(
            UserCourseModel.user_id == user_id,
            UserCourseModel.active == True
        )
        result = self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def get_by_course_id(self, course_id: UUID) -> List[UserCourseModel]:
        """Get all enrollments for a course"""
        stmt = select(UserCourseModel).where(UserCourseModel.course_id == course_id)
        result = self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def get_active_by_course_id(self, course_id: UUID) -> List[UserCourseModel]:
        """Get active enrollments for a course"""
        stmt = select(UserCourseModel).where(
            UserCourseModel.course_id == course_id,
            UserCourseModel.active == True
        )
        result = self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def get_by_user_and_course(self, user_id: UUID, course_id: UUID) -> Optional[UserCourseModel]:
        """Get enrollment for specific user and course"""
        stmt = select(UserCourseModel).where(
            UserCourseModel.user_id == user_id,
            UserCourseModel.course_id == course_id
        )
        result = self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def deactivate_enrollment(self, enrollment_id: UUID) -> bool:
        """Deactivate enrollment"""
        enrollment = await self.get_by_id(enrollment_id)
        if enrollment:
            enrollment.active = False
            self.session.flush()
            return True
        return False
    
    async def activate_enrollment(self, enrollment_id: UUID) -> bool:
        """Activate enrollment"""
        enrollment = await self.get_by_id(enrollment_id)
        if enrollment:
            enrollment.active = True
            self.session.flush()
            return True
        return False
    
    async def count_active_by_course_id(self, course_id: UUID) -> int:
        """Count active enrollments in a course"""
        stmt = select(func.count()).select_from(UserCourseModel).where(
            UserCourseModel.course_id == course_id,
            UserCourseModel.active == True
        )
        result = self.session.execute(stmt)
        return result.scalar() or 0
