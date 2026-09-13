from typing import Optional, List
from uuid import UUID
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import select, and_
from src.data.models.profiles_to_exclude_model import ProfilesToExcludeModel
from src.data.repositories.base.base_repository import BaseRepository
from src.infrastructure.handlers.datetime_handler import DateTimeHandler

class ProfilesToExcludeRepository(BaseRepository):
    def __init__(self, session: Session):
        super().__init__(session, ProfilesToExcludeModel)

    async def get_by_user_id(self, user_id: UUID) -> Optional[ProfilesToExcludeModel]:
        """Check if a user's profile is on the exclusion list."""
        stmt = select(ProfilesToExcludeModel).where(
            ProfilesToExcludeModel.user_id == user_id
        )
        result = self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_active_exclusions(self, skip: int = 0, limit: int = 100) -> List[ProfilesToExcludeModel]:
        """Get all active exclusion requests (not yet past the 48-hour window)."""
        # Active if created_at + 48h > now (from next day midnight)
        now = DateTimeHandler.now()
        cutoff = now - timedelta(hours=48)
        
        stmt = select(ProfilesToExcludeModel).where(
            ProfilesToExcludeModel.created_at > cutoff
        ).offset(skip).limit(limit)
        
        result = self.session.execute(stmt)
        return list(result.scalars().all())

    async def delete_exclusion(self, user_id: UUID) -> bool:
        """Remove a user from the exclusion list."""
        exclusion = await self.get_by_user_id(user_id)
        if exclusion:
            self.session.delete(exclusion)
            self.session.flush()
            return True
        return False

    async def is_within_cancellation_window(self, user_id: UUID) -> bool:
        """
        Check if a deactivation can still be cancelled.
        User can cancel within 48 hours starting from next day's midnight after deactivation.
        """
        exclusion = await self.get_by_user_id(user_id)
        if not exclusion:
            return False
        
        # Calculate next day's midnight after deactivation
        deactivation_date = exclusion.created_at.date()
        next_midnight = datetime.combine(deactivation_date + timedelta(days=1), datetime.min.time())
        
        # Window ends 48 hours after next midnight
        cancellation_deadline = next_midnight + timedelta(hours=48)

        # Make it timezone-aware (Brazil timezone)
        cancellation_deadline = cancellation_deadline.replace(tzinfo=DateTimeHandler.BRAZIL_TZ)

        return DateTimeHandler.now() <= cancellation_deadline

    async def get_exclusions_past_deadline(self) -> List[ProfilesToExcludeModel]:
        """Get exclusions that are past the cancellation window (ready for actual deletion)."""
        now = DateTimeHandler.now()
        
        # Get all exclusions
        all_exclusions = await self.get_all()
        
        past_deadline = []
        for exclusion in all_exclusions:
            deactivation_date = exclusion.created_at.date()
            next_midnight = datetime.combine(deactivation_date + timedelta(days=1), datetime.min.time())
            cancellation_deadline = next_midnight + timedelta(hours=48)
            
            if now > cancellation_deadline:
                past_deadline.append(exclusion)
        
        return past_deadline