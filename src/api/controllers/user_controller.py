"""User controller"""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Request, status, Query
from sqlalchemy.orm import Session

from src.application.services.user_service import UserService
from src.application.services.user_password_history_service import UserPasswordHistoryService
from src.data.models.user_model import UserModel
from src.data.repositories.profiles_to_exclude_repository import ProfilesToExcludeRepository
from src.data.repositories.user_repository import UserRepository
from src.data.repositories.user_password_history_repository import UserPasswordHistoryRepository
from src.data.db_context.database import get_db
from src.api.dependencies.auth_dependencies import get_current_active_user
from src.domain.schemas.user import DeactivateUser, User, UserCreate, UserUpdate
from src.domain.schemas.user_password_history import PasswordChange

router = APIRouter(
    prefix="/user",
    tags=["User"],
    dependencies=[Depends(get_current_active_user)]
)

def get_user_service(db: Session = Depends(get_db)) -> UserService:
    """Dependency injection for UserService"""
    user_repo = UserRepository(db)
    password_history_repo = UserPasswordHistoryRepository(db)
    password_history_service = UserPasswordHistoryService(password_history_repo)
    profiles_to_exclude_repo = ProfilesToExcludeRepository(db)

    return UserService(
        user_repo,
        password_history_service,
        profiles_to_exclude_repo
    )

@router.post("/", response_model=User, status_code=status.HTTP_201_CREATED)
async def create_user(
    dto: UserCreate,
    current_user: User = Depends(get_current_active_user),
    service: UserService = Depends(get_user_service)
):
    """
    Create a new user (Admin/Secretary only).
    Documents are auto-approved.
    """
    if current_user.user_type_id not in [1, 2]:
        raise HTTPException(status_code=403, detail="Não autorizado")
    
    try:
        return await service.create_user(dto, created_by_user_id=current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.patch("/{user_id}/deactivate")
async def deactivate_user(
    request: Request,
    user_id: UUID,
    dto: DeactivateUser,
    current_user: User = Depends(get_current_active_user),
    service: UserService = Depends(get_user_service)
):
    """
    Deactivate a user account. Admin (1), Secretary (2) only and Student (5).
    """
    if current_user.user_type_id not in [1, 2, 5]:
        raise HTTPException(status_code=403, detail="Não autorizado")
    
    # Validates if student user is deactivating their own account
    if current_user.user_type_id == 5:
        user: UserModel | None = await service.get_by_id(user_id)

        if not user:
            raise HTTPException(status_code=400, detail="Usuário não encontrado")

        if user.id != current_user.id:
            raise HTTPException(status_code=403, detail="Não autorizado")
    
    try:
        user_ip: str = request.client.host if request.client else "unknown"
        result: bool = await service.deactivate_user(
            user_id,
            dto,
            performed_by_user_id=current_user.id,
            user_ip_address=user_ip
        )

        return {"message": "Usuário desativado com sucesso", "success": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.patch("/{user_id}/activate")
async def activate_user(
    request: Request,
    user_id: UUID,
    current_user: User = Depends(get_current_active_user),
    service: UserService = Depends(get_user_service)
):
    """
    Activate a user account. Admin (1) and Secretary (2) only.
    """
    if current_user.user_type_id not in [1, 2]:
        raise HTTPException(status_code=403, detail="Não autorizado")
    
    try:
        user_ip: str = request.client.host if request.client else "unknown"
        result: bool = await service.activate_user(
            user_id,
            performed_by_user_id=current_user.id,
            user_ip_address=user_ip
        )

        return {"message": "Usuário ativado com sucesso", "success": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/list", response_model=List[User])
async def list_users(
    name: Optional[str] = Query(None),
    document: Optional[str] = Query(None),
    email: Optional[str] = Query(None),
    phoneNumber: Optional[str] = Query(None),
    user_type_id: Optional[int] = Query(None),
    active: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    service: UserService = Depends(get_user_service)
):
    """
    List users with filters and pagination.
    - Admin/Secretary: can list all
    - Coordinator/Educator: can list students only
    """
    # Admins and Secretaries can list all users
    if current_user.user_type_id in [1, 2]:
        return await service.find_users(
            name=name,
            document=document,
            email=email,
            phoneNumber=phoneNumber,
            user_type_id=user_type_id,
            active=active,
            page=page,
            page_size=page_size
        )
    
    # Coordinators and Educators can only list students
    if current_user.user_type_id in [3, 4]:
        return await service.find_users(
            name=name,
            document=document,
            email=email,
            phoneNumber=phoneNumber,
            user_type_id=5, # Students only
            active=active,
            page=page,
            page_size=page_size
        )
    
    raise HTTPException(status_code=403, detail="Não autorizado")

@router.get("/{user_id}", response_model=User)
async def get_user(
    user_id: UUID,
    current_user: User = Depends(get_current_active_user),
    service: UserService = Depends(get_user_service)
):
    """
    Get user by ID.
    - Staff can view any user
    - Users can view themselves
    """
    user: User | None = await service.get_by_id(user_id)

    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    if current_user.user_type_id not in [1, 2] and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Não autorizado")
    
    return user

@router.put("/{user_id}", response_model=User)
async def update_user(
    user_id: UUID,
    dto: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    service: UserService = Depends(get_user_service)
):
    """
    Update user information.
    - Admin/Secretary can update any user
    - Users can update themselves
    """
    if current_user.user_type_id not in [1, 2] and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Não autorizado")
    
    try:
        user: User | None = await service.update_user(user_id, dto)

        if not user:
            raise HTTPException(status_code=404, detail="Usuário não encontrado")
        
        return user
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.patch("/{user_id}/password")
async def change_password(
    user_id: UUID,
    dto: PasswordChange,
    current_user: User = Depends(get_current_active_user),
    service: UserService = Depends(get_user_service)
):
    """
    Change user password.
    - Users can only change their own password
    """
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Só pode alterar sua própria senha")
    
    try:
        result: bool = await service.change_password(user_id, dto)

        return {"message": "Senha alterada com sucesso", "success": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
