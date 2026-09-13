"""User password history repository"""
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import select, and_

from src.data.models.user_password_history_model import UserPasswordHistoryModel
from src.data.repositories.base.base_repository import BaseRepository

class UserPasswordHistoryRepository(BaseRepository):
    """Repository for User Password History entity"""
    
    def __init__(self, session: Session):
        super().__init__(session, UserPasswordHistoryModel)
    
    async def get_by_user_id(
        self, 
        user_id: UUID, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[UserPasswordHistoryModel]:
        """Get password history for a user, ordered by most recent first"""
        stmt = select(UserPasswordHistoryModel).where(
            UserPasswordHistoryModel.user_id == user_id
        ).order_by(UserPasswordHistoryModel.created_at.desc()).offset(skip).limit(limit)
        
        result = self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def get_recent_by_user_id(
        self, 
        user_id: UUID, 
        limit: int = 5
    ) -> List[UserPasswordHistoryModel]:
        """Get most recent password history entries for a user"""
        return await self.get_by_user_id(user_id, skip=0, limit=limit)
    
    async def get_oldest_by_user_id(
        self, 
        user_id: UUID, 
        limit: Optional[int] = None
    ) -> List[UserPasswordHistoryModel]:
        """Get oldest password history entries for a user (for cleanup)"""
        stmt = select(UserPasswordHistoryModel).where(
            UserPasswordHistoryModel.user_id == user_id
        ).order_by(UserPasswordHistoryModel.created_at.asc())
        
        if limit:
            stmt = stmt.limit(limit)
        
        result = self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def count_by_user_id(self, user_id: UUID) -> int:
        """Count password history entries for a user"""
        from sqlalchemy import func
        
        stmt = select(func.count()).select_from(UserPasswordHistoryModel).where(
            UserPasswordHistoryModel.user_id == user_id
        )
        result = self.session.execute(stmt)
        return result.scalar() or 0
    
    async def delete_old_entries(self, user_id: UUID, keep_count: int = 10) -> int:
        """Delete old password history entries, keeping the most recent ones"""
        # Get entries to delete (all except the most recent 'keep_count')
        old_entries = await self.get_oldest_by_user_id(user_id)
        
        if len(old_entries) <= keep_count:
            return 0
        
        # Delete excess entries
        entries_to_delete = old_entries[:len(old_entries) - keep_count]
        deleted_count = 0
        
        for entry in entries_to_delete:
            await self.delete(entry.id)
            deleted_count += 1
        
        return deleted_count
    
    async def is_password_reused(
        self, 
        user_id: UUID, 
        password_hash: str, 
        check_count: int = 5
    ) -> bool:
        """Check if password was used recently"""
        recent_passwords = await self.get_recent_by_user_id(user_id, limit=check_count)
        
        for history in recent_passwords:
            if history.password == password_hash:
                return True
        
        return False
    
    async def cleanup_old_passwords(self, user_id: UUID, max_history: int = 10) -> int:
        """Clean up old password entries, keeping only the most recent ones"""
        count = await self.count_by_user_id(user_id)
        
        if count > max_history:
            return await self.delete_old_entries(user_id, keep_count=max_history)
        
        return 0
