"""User course enrollment repository"""
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import func, select

from src.data.models.enrollment_model import EnrollmentModel
from src.data.repositories.base.base_repository import BaseRepository

class EnrollmentRepository(BaseRepository[EnrollmentModel]):
    """Repository for User Course enrollment entity"""
    
    def __init__(self, session: Session):
        super().__init__(session, EnrollmentModel)
    
    async def get_by_user_id(self, user_id: UUID) -> List[EnrollmentModel]:
        """Get all enrollments for a user"""
        stmt = select(EnrollmentModel).where(EnrollmentModel.user_id == user_id)
        result = self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def get_active_by_user_id(self, user_id: UUID) -> List[EnrollmentModel]:
        """Get active enrollments for a user"""
        stmt = select(EnrollmentModel).where(
            EnrollmentModel.user_id == user_id,
            EnrollmentModel.active == True
        )
        result = self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def get_by_course_id(self, course_id: UUID) -> List[EnrollmentModel]:
        """Get all enrollments for a course"""
        stmt = select(EnrollmentModel).where(EnrollmentModel.course_id == course_id)
        result = self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def get_active_by_course_id(self, course_id: UUID) -> List[EnrollmentModel]:
        """Get active enrollments for a course"""
        stmt = select(EnrollmentModel).where(
            EnrollmentModel.course_id == course_id,
            EnrollmentModel.active == True
        )
        result = self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def get_by_user_and_course(self, user_id: UUID, course_id: UUID) -> Optional[EnrollmentModel]:
        """Get enrollment for specific user and course"""
        stmt = select(EnrollmentModel).where(
            EnrollmentModel.user_id == user_id,
            EnrollmentModel.course_id == course_id
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
        stmt = select(func.count()).select_from(EnrollmentModel).where(
            EnrollmentModel.course_id == course_id,
            EnrollmentModel.active == True
        )
        result = self.session.execute(stmt)
        return result.scalar() or 0
