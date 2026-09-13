"""Authentication service - JWT token management and user authentication"""
from datetime import datetime, timedelta
from typing import Any, Optional
from uuid import UUID
import bcrypt
from jose import jwt, JWTError

from src.application.logging.application_logger import ApplicationLogger
from src.application.mappers.user_mapper import UserMapper
from src.data.models.user_model import UserModel
from src.data.repositories.profiles_to_exclude_repository import ProfilesToExcludeRepository
from src.data.repositories.user_repository import UserRepository
from src.domain.schemas.auth import Login
from src.domain.schemas.user import User
from src.infrastructure.configuration.settings import settings
from src.infrastructure.handlers.datetime_handler import DateTimeHandler

class AuthService:
    """Service for authentication and JWT token management"""
    
    def __init__(
        self,
        user_repo: UserRepository,
        profiles_to_exclude_repo: ProfilesToExcludeRepository = None
    ):
        self.user_repo = user_repo
        self.profiles_to_exclude_repo = profiles_to_exclude_repo
    
    async def create_access_token(self, user_id: UUID, user_type_id: int) -> str:
        """Create JWT access token"""
        try:
            now: datetime = DateTimeHandler.utc_now()
            expire: datetime = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
            payload: dict[str, Any] = {
                "sub": str(user_id),
                "user_type_id": user_type_id,
                "exp": int(expire.timestamp()),
                "iat": int(now.timestamp())
            }
            return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
        except Exception as e:
            await ApplicationLogger.log_error(e, reraise=True)
    
    async def create_refresh_token(self, user_id: UUID) -> str:
        """Create JWT refresh token"""
        try:
            now: datetime = DateTimeHandler.utc_now()
            expire: datetime = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
            payload: dict[str, Any] = {
                "sub": str(user_id),
                "exp": expire,
                "iat": DateTimeHandler.now(),
                "type": "refresh"
            }
            return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
        except Exception as e:
            await ApplicationLogger.log_error(e, reraise=True)
    
    async def verify_token(self, token: str) -> Optional[dict[str, Any]]:
        """Verify JWT token and return payload"""
        try:
            payload: dict[str, Any] = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM]
            )
            
            return payload
        except JWTError:
            return None
        except Exception as e:
            await ApplicationLogger.log_error(e, reraise=True)
    
    async def get_user_from_token(self, token: str) -> Optional[User]:
        """Get user from JWT token"""
        try:
            payload: dict[str, Any] | None = await self.verify_token(token)

            if not payload:
                return None
            
            user_id: str | None = payload.get("sub")

            if not user_id:
                return None
            
            user_model: UserModel | None = await self.user_repo.get_by_id(UUID(user_id))

            if not user_model:
                return None
            
            return UserMapper.model_to_schema(user_model)
        except Exception as e:
            await ApplicationLogger.log_error(e, reraise=True)
    
    async def authenticate(self, body: Login) -> Optional[dict[str, Any]]:
        """
        Authenticate user with document and password.
        
        Args:
            document: User's document (CPF)
            password: Plain text password
            
        Returns:
            Dict with tokens if authentication successful, None otherwise
        """
        try:
            # Find user by document
            user: UserModel | None = await self.user_repo.get_by_document(body.document)

            # Is user valid
            if not user or not user.active:
                return None
            
            # Verify password
            if not await self._verify_password(body.password, user.password):
                return None
            
            # Generate tokens
            user_uuid: UUID = user.id
            has_pending_deactivation: bool = await self.profiles_to_exclude_repo.is_within_cancellation_window(user_uuid)

            # Validates if a user has an active deactivation process
            if has_pending_deactivation:
                # Cancel the deactivation
                await self.profiles_to_exclude_repo.delete_exclusion(user_uuid)
                
                # Reactivate user
                await self.user_repo.activate(user_uuid)
                
                # Log reactivation
                from src.data.repositories.log_user_activation_repository import LogUserActivationRepository

                log_repo: LogUserActivationRepository = LogUserActivationRepository(self.user_repo.session)
                await log_repo.log(
                    deactivation_reason=None,
                    activated=True,
                    user_id=user.id,
                    performed_by_user_id=user.id,
                    performed_by_user_ip_address="self_login"
                )
                self.user_repo.session.commit()

            access_token: str = await self.create_access_token(user_uuid, user.user_type_id)
            refresh_token: str = await self.create_refresh_token(user_uuid)
            
            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
                "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                "user": {
                    "id": str(user_uuid),
                    "name": user.name,
                    "email": user.email,
                    "user_type_id": user.user_type_id
                }
            }
        except Exception as e:
            await ApplicationLogger.log_error(e, reraise=True)
    
    async def refresh_access_token(self, refresh_token: str) -> Optional[dict[str, Any]]:
        """
        Refresh access token using refresh token.
        
        Args:
            refresh_token: The refresh token
            
        Returns:
            Dict with new tokens if successful, None otherwise
        """
        try:
            payload: dict[str, Any] = await self.verify_token(refresh_token)

            if not payload or payload.get("type") != "refresh":
                return None
            
            user_id: str = payload.get("sub")

            if not user_id:
                return None
            
            user: UserModel = await self.user_repo.get_by_id(UUID(user_id))

            if not user or not user.active:
                return None
            
            # Create new tokens
            access_token: str = await self.create_access_token(UUID(user_id), user.user_type_id)
            new_refresh_token: str = await self.create_refresh_token(UUID(user_id))
            
            return {
                "access_token": access_token,
                "refresh_token": new_refresh_token,
                "token_type": "bearer",
                "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
            }
        except Exception as e:
            await ApplicationLogger.log_error(e, reraise=True)

    # Private methods
    async def _verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verify a plain password against a hashed password.
        
        Args:
            plain_password: The plain text password
            hashed_password: The hashed password to compare against
            
        Returns:
            True if password matches, False otherwise
        """
        return bcrypt.checkpw(
            plain_password.encode('utf-8'),
            hashed_password.encode('utf-8')
        )
