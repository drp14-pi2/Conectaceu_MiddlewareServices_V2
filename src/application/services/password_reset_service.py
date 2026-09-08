"""Password reset service - handles forgot password flow"""
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID
import secrets

from src.application.logging.application_logger import ApplicationLogger
from src.data.models.user_model import UserModel
from src.data.repositories.user_repository import UserRepository
from src.application.services.user_password_history_service import UserPasswordHistoryService
from src.domain.schemas.password_reset import PasswordResetRequest
from src.infrastructure.handlers.password_hasher import PasswordHasher
from src.infrastructure.messaging.email.email_service import EmailService
from src.infrastructure.configuration.settings import settings
from src.infrastructure.handlers.datetime_handler import DateTimeHandler

class PasswordResetService:
    """Service for password reset flow"""
    
    def __init__(
        self,
        user_repo: UserRepository,
        password_history_service: UserPasswordHistoryService,
        email_service: EmailService
    ):
        self.user_repo = user_repo
        self.password_history_service = password_history_service
        self.email_service = email_service
    
    async def request_password_reset(self, body: PasswordResetRequest) -> dict:
        """
        Request password reset by email.
        Generates reset token and sends email.
        
        Args:
            email: User's email
            
        Returns:
            Dict with status message
        """
        try:
            RETURN_MESSAGE: str = "Se o e-mail estiver na nossa base de dados, uma mensagem será enviada"
            # Find user by email
            user: UserModel | None = await self.user_repo.get_by_email(body.email)

            # Doesn't reveal if the user exists or not for security
            if not user or not user.active:
                return {"message": RETURN_MESSAGE}
            
            # Generate reset token
            reset_token: str = secrets.token_urlsafe(32)
            token_expiry: datetime = DateTimeHandler.utc_now() + timedelta(hours=1)
            # Save token to user
            user.password_reset_token = reset_token
            user.password_reset_expires = token_expiry
            await self.user_repo.update(user)
            self.user_repo.session.commit()
            # Send email
            await self.email_service.send_password_reset_email(
                to_email=user.email,
                reset_token=reset_token,
                frontend_url=settings.APP_FRONTEND_URL
            )
            
            return {"message": RETURN_MESSAGE}
        except Exception as e:
            await ApplicationLogger.log_error(e, reraise=True)
    
    async def validate_reset_token(self, token: str) -> dict[str, Any]:
        """
        Validate password reset token.
        
        Args:
            token: Reset token from email
            
        Returns:
            Dict with validation result
        """
        try:
            # Find user by reset token
            user: UserModel | None= await self.user_repo.find_by_password_reset_token(token)

            if not user:
                return {"valid": False, "reason": "Token inválido ou expirado"}
            
            # Check if token is expired
            if user.password_reset_expires:
                expires: datetime = user.password_reset_expires.replace(tzinfo=DateTimeHandler.UTC_TZ)

                if expires < DateTimeHandler.utc_now():
                    return {"valid": False, "reason": "Token expirado"}
            
            return {
                "valid": True,
                "user_id": str(UUID(bytes=user.id)),
                "message": "Token válido"
            }
        except Exception as e:
            await ApplicationLogger.log_error(e, reraise=True)
    
    async def reset_password(self, token: str, new_password: str) -> dict:
        """
        Reset password using token.
        
        Args:
            token: Reset token from email
            new_password: New plain text password
            
        Returns:
            Dict with result status
        """
        try:
            # Validate token
            validation: dict[str, Any] = await self.validate_reset_token(token)

            if not validation["valid"]:
                return {"success": False, "reason": validation["reason"]}
            
            user_id: UUID = UUID(validation["user_id"])
            user: UserModel | None = await self.user_repo.get_by_id(user_id)
            
            # Validate password strength
            self._validate_password(new_password)
            
            # Check password history
            validation_result: dict[str, Any] = await self.password_history_service.validate_password_change(
                user_id=user_id,
                new_plain_password=new_password,
                history_check_count=5
            )
            
            if not validation_result["valid"]:
                return {"success": False, "reason": validation_result["reason"]}
            
            # Hash and update password
            from src.application.services.auth_service import AuthService
            hashed_password: str = PasswordHasher.hash_password(new_password)
            
            success: bool = await self.user_repo.update_password(user_id, hashed_password)
            self.user_repo.session.commit()
            
            if success:
                # Add to password history
                await self.password_history_service.add_password_hash_to_history(
                    user_id=user_id,
                    hashed_password=hashed_password
                )
                
                # Clear reset token
                user.password_reset_token = None
                user.password_reset_expires = None
                await self.user_repo.update(user)
                self.user_repo.session.commit()
                
                return {"success": True, "message": "Senha atualizada com sucesso!"}
            
            return {"success": False, "reason": "Falha ao atualizar senha"}
        except Exception as e:
            await ApplicationLogger.log_error(e, reraise=True)

    def _validate_password(self, password: str) -> None:
        """
        Validate if passwords match and password strength requirements:
        - 8 to 128 characters
        - At least one lowercase letter
        - At least one uppercase letter
        - At least one number
        - At least one special character
        """
        import re
        
        # Check length
        if len(password) < 8:
            raise ValueError("A senha deve conter pelo menos 8 caracteres")
        
        if len(password) > 128:
            raise ValueError("A senha deve conter no máximo 128 caracteres")
        
        # Check lowercase
        if not re.search(r'[a-z]', password):
            raise ValueError("A senha deve conter pelo menos uma letra minúscula")
        
        # Check uppercase
        if not re.search(r'[A-Z]', password):
            raise ValueError("A senha deve conter pelo menos uma letra maiúscula")
        
        # Check number
        if not re.search(r'\d', password):
            raise ValueError("A senha deve conter pelo menos um número")
        
        # Check special character
        if not re.search(r'[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\;/\'`~]', password):
            raise ValueError("A senha deve conter pelo menos um caractere especial")
