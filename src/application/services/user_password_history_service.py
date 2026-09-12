"""User password history service - business logic for User Password History entity"""
from typing import Any, List
from uuid import UUID
import bcrypt

from src.application.logging.application_logger import ApplicationLogger
from src.data.models.user_password_history_model import UserPasswordHistoryModel
from src.data.repositories.user_password_history_repository import UserPasswordHistoryRepository
from src.application.services.base_service import BaseService
from src.domain.schemas.user_password_history import UserPasswordHistory, UserPasswordHistoryCreate
from src.infrastructure.handlers.datetime_handler import DateTimeHandler
from src.application.mappers.user_password_history_mapper import UserPasswordHistoryMapper
from src.infrastructure.handlers.password_hasher import PasswordHasher

class UserPasswordHistoryService(BaseService):
    """Service for User Password History business logic"""
    
    def __init__(self, repository: UserPasswordHistoryRepository):
        super().__init__(repository, 'user_password_history', UserPasswordHistoryMapper)
        self.repository = repository
    
    async def is_password_reused(
        self,
        user_id: UUID,
        plain_password: str,
        check_count: int = 10
    ) -> bool:
        """
        Check if a plain password matches any recent password in history.
        
        Args:
            user_id: The user's ID
            plain_password: The plain text password to check
            check_count: Number of recent passwords to check (default: 10)
            
        Returns:
            True if password was recently used, False otherwise
        """
        try:
            # Get recent password history
            recent_history: List[UserPasswordHistoryModel] = await self.repository.get_recent_by_user_id(user_id, check_count)
            
            # Check each historical password against the plain password
            for history_entry in recent_history:
                return self._verify_password(plain_password, history_entry.password)
            
            return False
        except Exception as e:
            await ApplicationLogger.log_error(e, reraise=True)
    
    async def add_password_hash_to_history(
        self,
        user_id: UUID,
        hashed_password: str
    ) -> UserPasswordHistory:
        """
        Add an already hashed password to the user's password history.
        Use this when the password is already hashed (e.g., during user creation).
        
        Args:
            user_id: The user's ID
            hashed_password: The already hashed password
            
        Returns:
            The created password history entry
        """
        try:
            from uuid import uuid4
            is_password_hashed: bool = PasswordHasher.is_bcrypt_hash(hashed_password)

            if not is_password_hashed:
                hashed_password = PasswordHasher.hash_password(hashed_password)

            dto: UserPasswordHistoryCreate = UserPasswordHistoryCreate(
                password=hashed_password,
                user_id=user_id
            )
            model: UserPasswordHistoryModel = UserPasswordHistoryMapper.create_to_model(dto)
            saved_model: UserPasswordHistoryModel = await self.repository.create(model)
            # Cleanup old passwords (keep only last 10)
            await self._cleanup_old_passwords(user_id, max_history=10)
            self.repository.session.commit()
            
            return UserPasswordHistoryMapper.model_to_schema(saved_model)
        except Exception as e:
            await ApplicationLogger.log_error(e, reraise=True)
    
    async def validate_password_change(
        self,
        user_id: UUID,
        new_plain_password: str,
        history_check_count: int = 5
    ) -> dict[str, Any]:
        """
        Validate a password change against history rules.
        
        Args:
            user_id: The user's ID
            new_plain_password: The new plain text password
            history_check_count: Number of recent passwords to check against
            
        Returns:
            Dict with validation results: {'valid': bool, 'reason': str}
        """
        try:
            new_password_length: int = len(new_plain_password)

            # Check minimum length
            if new_password_length < 8:
                return {'valid': False, 'reason': 'Password must be at least 8 characters'}
            
            # Check maximum length
            if new_password_length > 100:
                return {'valid': False, 'reason': 'Password must be at most 100 characters'}
            
            # Check for password reuse
            is_reused: bool = await self.is_password_reused(user_id, new_plain_password, history_check_count)

            if is_reused:
                return {'valid': False, 'reason': f'Password was used in the last {history_check_count} passwords'}
            
            return {'valid': True, 'reason': 'Password is valid'}
        except Exception as e:
            await ApplicationLogger.log_error(e, reraise=True)

    # Private methods
    async def _cleanup_old_passwords(self, user_id: UUID, max_history: int = 10) -> int:
        """
        Clean up old password entries, keeping only the most recent ones.
        
        Args:
            user_id: The user's ID
            max_history: Maximum number of password history entries to keep
            
        Returns:
            Number of deleted entries
        """
        try:
            cleaned_count: int = await self.repository.cleanup_old_passwords(user_id, max_history)
            self.repository.session.commit()

            return cleaned_count
        except Exception as e:
            await ApplicationLogger.log_error(e, reraise=True)
    
    def _verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verify a plain password against a hashed password.
        
        Args:
            plain_password: The plain text password
            hashed_password: The hashed password to compare against
            
        Returns:
            True if password matches, False otherwise
        """
        try:
            return bcrypt.checkpw(
                plain_password.encode('utf-8'),
                hashed_password.encode('utf-8')
            )
        except Exception:
            return False
