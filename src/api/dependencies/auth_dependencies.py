"""Authentication dependencies for FastAPI"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from src.application.services.auth_service import AuthService
from src.data.repositories.user_repository import UserRepository
from src.data.repositories.user_type_repository import UserTypeRepository
from src.data.db_context.database import get_db
from src.domain.schemas.user import User

security = HTTPBearer()

def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    """Get AuthService instance"""
    user_repo = UserRepository(db)
    
    return AuthService(user_repo)

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthService = Depends(get_auth_service)
) -> User:
    """Get current authenticated user from token"""
    token = credentials.credentials
    user = await auth_service.get_user_from_token(token)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    return user

async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current active user (raises 403 if deactivated)"""
    if not current_user.active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated"
        )
    
    return current_user

def require_permission(*permissions: str):
    """
    Dependency factory for requiring specific permissions.
    Usage: Depends(require_permission("register_user", "validate_user_documents"))
    """
    async def permission_checker(
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
    ) -> User:
        user_type_repo = UserTypeRepository(db)
        user_type = await user_type_repo.get_by_id_int(current_user.user_type_id)
        
        if not user_type:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User type not found"
            )
        
        for permission in permissions:
            if not getattr(user_type, permission[0], False):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Missing required permission: {permission}"
                )
        
        return current_user
    
    return permission_checker

def require_role(*roles: int):
    """
    Dependency factory for requiring specific user type IDs.
    Usage: Depends(require_role(1, 2))  # Admin or Secretary
    """
    async def role_checker(
        current_user: User = Depends(get_current_active_user)
    ) -> User:
        if current_user.user_type_id not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient role"
            )
        return current_user
    
    return role_checker
