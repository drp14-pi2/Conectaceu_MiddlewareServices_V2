"""Password reset controller"""
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.services.password_reset_service import PasswordResetService
from src.application.services.user_password_history_service import UserPasswordHistoryService
from src.data.db_context.database import get_db
from src.data.repositories.user_password_history_repository import UserPasswordHistoryRepository
from src.data.repositories.user_repository import UserRepository
from src.domain.schemas.password_reset import PasswordResetRequest
from src.domain.schemas.password_reset import PasswordResetRequest, PasswordResetSubmit
from src.infrastructure.messaging.email.email_service import EmailService
from src.api.middleware.rate_limiter import limiter

router = APIRouter(prefix="/password", tags=["Password Reset"])

def get_password_reset_service(db: AsyncSession = Depends(get_db)) -> PasswordResetService:
    user_repo = UserRepository(db)
    user_password_history_repository = UserPasswordHistoryRepository(db)
    password_history_service = UserPasswordHistoryService(user_password_history_repository)
    email_service = EmailService()
    
    return PasswordResetService(user_repo, password_history_service, email_service)

@router.post("/reset/request")
@limiter.limit("5/minute")
async def request_password_reset(
    request: Request,
    body: PasswordResetRequest,
    service: PasswordResetService = Depends(get_password_reset_service)
):
    """Request password reset by email."""
    return await service.request_password_reset(body)

@router.get("/reset/validate")
@limiter.limit("5/minute")
async def validate_reset_token(
    request: Request,
    token: str,
    service: PasswordResetService = Depends(get_password_reset_service)
):
    """Validate password reset token"""
    result: dict[str, Any] = await service.validate_reset_token(token)

    if not result["valid"]:
        raise HTTPException(status_code=400, detail=result["reason"])
    
    return result

@router.post("/reset")
@limiter.limit("5/minute")
async def reset_password(
    request: Request,
    body: PasswordResetSubmit,
    service: PasswordResetService = Depends(get_password_reset_service)
):
    """Reset password using token"""
    if body.new_password != body.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")
    
    result: dict[str, Any] = await service.reset_password(body.token, body.new_password)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["reason"])
    
    return {"message": result["message"]}
