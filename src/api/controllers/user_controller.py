"""User controller"""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Request, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.services.email_validation_service import EmailValidationService
from src.application.services.security_service import SecurityService
from src.application.services.user_service import UserService
from src.application.services.user_password_history_service import UserPasswordHistoryService
from src.data.models.user_model import UserModel
from src.data.repositories.class_repository import ClassRepository
from src.data.repositories.course_component_repository import CourseComponentRepository
from src.data.repositories.course_repository import CourseRepository
from src.data.repositories.document_repository import DocumentRepository
from src.data.repositories.document_validation_repository import DocumentValidationRepository
from src.data.repositories.enrollment_repository import EnrollmentRepository
from src.data.repositories.legal_representative_repository import LegalRepresentativeRepository
from src.data.repositories.profiles_to_exclude_repository import ProfilesToExcludeRepository
from src.data.repositories.user_repository import UserRepository
from src.data.repositories.user_password_history_repository import UserPasswordHistoryRepository
from src.data.repositories.email_validation_repository import EmailValidationRepository
from src.data.repositories.educational_unit_repository import EducationalUnitRepository
from src.data.db_context.database import get_db
from src.api.dependencies.auth_dependencies import get_current_active_user
from src.domain.schemas.user import DeactivateUser, User, UserCreate, UserList, UserUpdate
from src.domain.schemas.user_password_history import PasswordChange
from src.infrastructure.messaging.email.email_service import EmailService
from src.api.middleware.rate_limiter import limiter

router = APIRouter(
    prefix="/user",
    tags=["User"],
    dependencies=[Depends(get_current_active_user)]
)

def get_user_service(db: AsyncSession = Depends(get_db)) -> UserService:
    """Dependency injection for UserService"""
    user_repo = UserRepository(db)
    password_history_repo = UserPasswordHistoryRepository(db)
    password_history_service = UserPasswordHistoryService(password_history_repo)
    profiles_to_exclude_repo = ProfilesToExcludeRepository(db)
    educational_unit_repo = EducationalUnitRepository(db)
    document_depo = DocumentRepository(db)
    representative_repo = LegalRepresentativeRepository(db)
    doc_validation_repo = DocumentValidationRepository(db)

    return UserService(
        user_repo,
        password_history_service,
        profiles_to_exclude_repo,
        educational_unit_repo,
        document_depo,
        representative_repo,
        doc_validation_repo
    )

def get_email_validation_service(db: AsyncSession = Depends(get_db)) -> EmailValidationService:
    """Dependecy injection for EmailValidationService"""
    email_validation_repo = EmailValidationRepository(db)
    user_repo = UserRepository(db)
    email_service = EmailService()

    return EmailValidationService(
        email_validation_repo,
        user_repo,
        email_service
    )

def get_security_service(db: AsyncSession = Depends(get_db)) -> SecurityService:
    """Dependency injection for SecurityService"""
    class_repo = ClassRepository(db)
    component_repo = CourseComponentRepository(db)
    course_repo = CourseRepository(db)
    user_repo = UserRepository(db)
    document_repo = DocumentRepository(db)
    enrollment_repo = EnrollmentRepository(db)
    representative_repo = LegalRepresentativeRepository(db)

    return SecurityService(
        class_repo,
        component_repo,
        course_repo,
        user_repo,
        document_repo,
        enrollment_repo,
        representative_repo
    )

@router.post("/", response_model=User, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def create_user(
    request: Request,
    dto: UserCreate,
    current_user: User = Depends(get_current_active_user),
    service: UserService = Depends(get_user_service),
    security_service: SecurityService = Depends(get_security_service)
):
    """
    Create a new user (Admin/Secretary only).
    Documents are auto-approved.
    """
    if not await security_service.can_access_educational_unit(current_user.id, dto.educational_unit_id):
        raise HTTPException(status_code=403, detail="Só pode interagir com seu próprio polo")

    if current_user.user_type_id not in [1, 2]:
        raise HTTPException(status_code=403, detail="Não autorizado")
    
    try:
        return await service.create_user(dto, created_by_user_id=current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.patch("/{user_id}/deactivate")
@limiter.limit("5/minute")
async def deactivate_user(
    request: Request,
    user_id: UUID,
    dto: DeactivateUser,
    current_user: User = Depends(get_current_active_user),
    service: UserService = Depends(get_user_service),
    security_service: SecurityService = Depends(get_security_service)
):
    """
    Deactivate a user account. Admin (1), Secretary (2) only and Student (5).
    """
    if not await security_service.can_access_other_user(current_user.id, user_id):
        raise HTTPException(status_code=403, detail="Só pode interagir com seu próprio polo")

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
@limiter.limit("5/minute")
async def activate_user(
    request: Request,
    user_id: UUID,
    current_user: User = Depends(get_current_active_user),
    service: UserService = Depends(get_user_service),
    security_service: SecurityService = Depends(get_security_service)
):
    """
    Activate a user account. Admin (1) and Secretary (2) only.
    """
    if not await security_service.can_access_other_user(current_user.id, user_id):
        raise HTTPException(status_code=403, detail="Só pode interagir com seu próprio polo")

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


@router.post("/list", response_model=List[User])
@limiter.limit("20/minute")
async def list_users(
    request: Request,
    dto: UserList,
    current_user: User = Depends(get_current_active_user),
    service: UserService = Depends(get_user_service),
    security_service: SecurityService = Depends(get_security_service)
):
    """
    List users with filters and pagination.
    - Admin/Secretary: can list all
    - Coordinator/Educator: can list students only
    """
    if current_user.user_type_id != 1:
        if not dto.educational_units_ids:
            raise HTTPException(status_code=403, detail='IDs de polos são obrigatórios')
        elif any(unit_id != current_user.educational_unit_id for unit_id in dto.educational_units_ids):
            raise HTTPException(status_code=403, detail="Só pode interagir com seu próprio polo")

    # Admins and Secretaries can list all users
    if current_user.user_type_id in [1, 2]:
        return await service.find_users(
            name=dto.name,
            document=dto.document,
            email=dto.email,
            phoneNumber=dto.phoneNumber,
            user_type_id=dto.user_type_id,
            active=dto.active,
            educational_units_ids=dto.educational_units_ids,
            page=dto.page,
            page_size=dto.page_size
        )
    
    # Coordinators and Educators can only list students
    if current_user.user_type_id in [3, 4]:
        return await service.find_users(
            name=dto.name,
            document=dto.document,
            email=dto.email,
            phoneNumber=dto.phoneNumber,
            user_type_id=5, # Students only
            active=dto.active,
            page=dto.page,
            page_size=dto.page_size
        )
    
    raise HTTPException(status_code=403, detail="Não autorizado")

@router.get("/{user_id}", response_model=User)
@limiter.limit("20/minute")
async def get_user(
    request: Request,
    user_id: UUID,
    current_user: User = Depends(get_current_active_user),
    service: UserService = Depends(get_user_service),
    security_service: SecurityService = Depends(get_security_service)
):
    """
    Get user by ID.
    - Staff can view any user
    - Users can view themselves
    """
    if not await security_service.can_access_other_user(current_user.id, user_id):
        raise HTTPException(status_code=403, detail="Só pode interagir com seu próprio polo")

    user: User | None = await service.get_by_id(user_id)

    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    if current_user.user_type_id not in [1, 2] and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Não autorizado")
    
    return user

@router.put("/{user_id}", response_model=User)
@limiter.limit("5/minute")
async def update_user(
    request: Request,
    user_id: UUID,
    dto: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    service: UserService = Depends(get_user_service),
    security_service: SecurityService = Depends(get_security_service)
):
    """
    Update user information.
    - Admin/Secretary can update any user
    - Users can update themselves
    """
    if not await security_service.can_access_other_user(current_user.id, user_id):
        raise HTTPException(status_code=403, detail="Só pode interagir com seu próprio polo")

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
@limiter.limit("5/minute")
async def change_password(
    request: Request,
    user_id: UUID,
    dto: PasswordChange,
    current_user: User = Depends(get_current_active_user),
    service: UserService = Depends(get_user_service),
    security_service: SecurityService = Depends(get_security_service)
):
    """
    Change user password.
    - Users can only change their own password
    """
    if not await security_service.can_access_other_user(current_user.id, user_id):
        raise HTTPException(status_code=403, detail="Só pode interagir com seu próprio polo")

    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Só pode alterar sua própria senha")
    
    try:
        result: bool = await service.change_password(user_id, dto)

        return {"message": "Senha alterada com sucesso", "success": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/email/validation/{user_id}/request")
@limiter.limit("5/minute")
async def request_email_validation(
    request: Request,
    user_id: UUID,
    current_user: User = Depends(get_current_active_user),
    service: EmailValidationService = Depends(get_email_validation_service),
    security_service: SecurityService = Depends(get_security_service)
):
    """Request e-mail validation"""
    if current_user.id != user_id and not await security_service.can_access_other_user(current_user.id, user_id):
        raise HTTPException(status_code=403, detail="Só pode interagir com seu próprio polo")
    
    try:
        await service.request_email_validation(user_id)

        return {"message": "Verificação de e-mail requerida com sucesso!"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/email/validation/{user_id}/{token}")
@limiter.limit("5/minute")
async def activate_email(
    request: Request,
    user_id: UUID,
    token: str,
    current_user: User = Depends(get_current_active_user),
    service: EmailValidationService = Depends(get_email_validation_service),
    security_service: SecurityService = Depends(get_security_service)
):
    """Validates an e-mail given a token"""
    if current_user.id != user_id and not await security_service.can_access_other_user(current_user.id, user_id):
        raise HTTPException(status_code=403, detail="Só pode interagir com seu próprio polo")
    
    try:
        await service.validate_email(token, user_id)

        return {"message": "E-mail validado com sucesso!"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
