from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from src.data.models.enrollment_waiting_list_model import EnrollmentWaitingListModel
from src.data.repositories.base.base_repository import BaseRepository

class EnrollmentWaitingListRepository(BaseRepository):
    def __init__(self, session: AsyncSession):
        super().__init__(session, EnrollmentWaitingListModel)
    
    async def get_next_in_line(self, course_id: UUID) -> Optional[EnrollmentWaitingListModel]:
        """Get the user at the front of the waiting list for a class."""
        stmt = (
            select(EnrollmentWaitingListModel)
            .where(EnrollmentWaitingListModel.course_id == course_id)
            .order_by(EnrollmentWaitingListModel.position)
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_by_user_and_course(self, user_id: UUID, course_id: UUID) -> Optional[EnrollmentWaitingListModel]:
        """Check if user is already on the waiting list."""
        stmt = select(EnrollmentWaitingListModel).where(
            and_(
                EnrollmentWaitingListModel.user_id == user_id,
                EnrollmentWaitingListModel.course_id == course_id
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_last_position(self, course_id: UUID) -> int:
        """Get the last position number for a class."""
        stmt = (
            select(func.max(EnrollmentWaitingListModel.position))
            .where(EnrollmentWaitingListModel.course_id == course_id)
        )
        result = await self.session.execute(stmt)
        last = result.scalar()
        return last or 0
    
    async def remove_user(self, user_id: UUID, course_id: UUID) -> bool:
        """Remove a user from the waiting list."""
        entry = await self.get_by_user_and_course(user_id, course_id)
        if entry:
            await self.session.delete(entry)
            await self.session.flush()
            return True
        return False