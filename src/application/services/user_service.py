"""User service - business logic for User entity"""
import re
from typing import Any, List, Optional
from uuid import UUID
import bcrypt

from src.application.logging.application_logger import ApplicationLogger
from src.application.mappers.user_mapper import UserMapper
from src.application.services.user_password_history_service import UserPasswordHistoryService
from src.data.models.profiles_to_exclude_model import ProfilesToExcludeModel
from src.data.models.user_model import UserModel
from src.data.repositories.profiles_to_exclude_repository import ProfilesToExcludeRepository
from src.data.repositories.user_repository import UserRepository
from src.application.services.base_service import BaseService
from src.domain.schemas.user import DeactivateUser, User, UserCreate, UserUpdate
from src.infrastructure.handlers.datetime_handler import DateTimeHandler
from src.infrastructure.handlers.password_hasher import PasswordHasher
from src.domain.schemas.user_password_history import PasswordChange
from src.domain.schemas.address import AddressCreate

class UserService(BaseService):
    """Service for User business logic"""
    
    def __init__(
        self,
        repository: UserRepository,
        password_history_service: UserPasswordHistoryService,
        profiles_to_exclude_repo: ProfilesToExcludeRepository
    ):
        super().__init__(repository, 'user', mapper_class=UserMapper)
        self.repository = repository
        self.password_history_service = password_history_service
        self.profiles_to_exclude_repo = profiles_to_exclude_repo
    
    async def create_user(
        self, 
        dto: UserCreate, 
        created_by_user_id: Optional[UUID] = None
    ) -> User:
        """
        Create a new user with different flows based on who creates them.
        
        Args:
            dto: User creation data
            created_by_user_id: ID of the user creating this account (None for public registration)
        """
        try:
            # Normalize fields
            dto.document = re.sub(r'\D', '', dto.document)
            dto.name = dto.name.title()
            dto.address.street = dto.address.street.title()
            dto.address.neighborhood = dto.address.neighborhood.title()
            self._validate_password(dto.password)
            # Hash passwords
            dto.password = PasswordHasher.hash_password(dto.password)

            # Check if document already exists
            existing_user: UserModel | None = await self.repository.get_by_document(dto.document)

            if existing_user:
                raise ValueError("Documento pertence a outra pessoa")
            
            # Check if e-mail already exists
            if dto.email:
                existing_user = await self.repository.get_by_email(dto.email)

                if existing_user:
                    raise ValueError("E-mail pertence a outra pessoa")
            
            # Determine creation path
            is_public_creation = created_by_user_id is None
            
            # Validate creator
            if is_public_creation:
                is_creator_admin_or_secretary = False
            else:
                creator: UserModel | None = await self.repository.get_by_id(created_by_user_id)

                if not creator:
                    raise ValueError("Usuário criador não encontrado")
                
                if not creator.active:
                    raise ValueError("Usuário criador não está ativo")
                
                # Only Admin (1) and Secretary (2) can create users
                if creator.user_type_id not in [1, 2]:
                    raise ValueError("Este usuário não pode criar outros usuários")
                
                is_creator_admin_or_secretary = True
            # Create User
            model: UserModel = UserMapper.create_to_model(dto)
            is_creating_student = model.user_type_id == 5

            if model.email != '' and not is_creator_admin_or_secretary:
                model.email_verified = False

            if is_creating_student:
                model.student_sequential = await self._get_new_student_sequential()
            
            # Set user status based on creator role
            is_minor: bool = (DateTimeHandler.now().date() - dto.birthdate).days < (18 * 365)
            
            if is_creator_admin_or_secretary and not is_minor:
                model.active = True
            else:
                model.active = False
            
            # Save user
            saved_model: UserModel = await self.repository.create(model)
            user_id = UUID(bytes=saved_model.id)
            
            # Save password history
            await self.password_history_service.add_password_hash_to_history(
                user_id=user_id,
                hashed_password=model.password
            )
            # Create Address
            await self._create_address(dto.address)
            self.repository.session.commit()

            return UserMapper.model_to_schema(saved_model)
        except Exception as e:
            await ApplicationLogger.log_error(e, reraise=True)
    
    async def update_user(self, user_id: UUID, dto: UserUpdate) -> User:
        """Update user with business validation"""
        try:
            model: UserModel | None = await self.repository.get_by_id(user_id)

            if not model:
                raise ValueError("Usuário não encontrado")
            
            # Check email uniqueness if being updated
            if dto.email:
                existing: UserModel | None = await self.repository.get_by_email(dto.email)

                if existing and existing.id != model.id:
                    raise ValueError("E-mail já registrado")
            
            updated_model: UserModel = UserMapper.create_to_model(dto)
            saved_model: UserModel = await self.repository.update(updated_model)
            self.repository.session.commit()
            
            return UserMapper.model_to_schema(saved_model)
        except Exception as e:
            await ApplicationLogger.log_error(e, reraise=True)
    
    async def change_password(self, user_id: UUID, dto: PasswordChange) -> bool:
        """Change user password with validation"""
        try:
            user: UserModel | None = await self.repository.get_by_id(user_id)

            if not user:
                raise ValueError("Usuário não encontrado")
            
            # Validate new password against history
            validation: dict[str, Any] = await self.password_history_service.validate_password_change(
                user_id=user_id,
                new_plain_password=dto.new_password,
                history_check_count=10
            )
            
            if not validation['valid']:
                raise ValueError(validation['reason'])
            
            # Hash and update password
            hashed_password: str = PasswordHasher.hash_password(dto.new_password)
            success: bool = await self.repository.update_password(user_id, hashed_password)

            if success:
                # Add to password history
                await self.password_history_service.add_password_hash_to_history(
                    user_id=user_id,
                    hashed_password=hashed_password
                )

            self.repository.session.commit()
            
            return success
        except Exception as e:
            await ApplicationLogger.log_error(e, reraise=True)
    
    async def deactivate_user(
        self,
        user_id: UUID,
        dto: DeactivateUser,
        performed_by_user_id: Optional[UUID] = None,
        user_ip_address: Optional[str] = None
    ) -> bool:
        """Deactivate user account and add to exclusion list"""
        user: UserModel | None = await self.repository.get_by_id(user_id)

        if not user:
            raise ValueError("Usuário não encontrado")
        
        if not user.active:
            raise ValueError("Conta de usuário já desativada")
        
        # Deactivate user
        success: bool = await self.repository.deactivate(user_id)
        
        # Add to profiles to exclude
        if success:
            from uuid import uuid4
            
            exclusion_model = ProfilesToExcludeModel(
                id=uuid4().bytes,
                created_at=DateTimeHandler.now(),
                user_id=user_id,
                processed=False
            )
            await self.profiles_to_exclude_repo.create(exclusion_model)
        
        # Log activation change
        if success and performed_by_user_id:
            from src.data.repositories.log_user_activation_repository import LogUserActivationRepository
            log_repo = LogUserActivationRepository(self.repository.session)
            await log_repo.log(
                deactivation_reason=dto.reason,
                activated=False,
                user_id=user_id.bytes,
                performed_by_user_id=performed_by_user_id.bytes,
                performed_by_user_ip_address=user_ip_address or "unknown"
            )

        self.repository.session.commit()
        
        return success
        
    async def activate_user(
        self, 
        user_id: UUID,
        performed_by_user_id: Optional[UUID] = None,
        user_ip_address: Optional[str] = None
    ) -> bool:
        """Activate user account"""
        try:
            user: UserModel | None = await self.repository.get_by_id(user_id)

            if not user:
                raise ValueError("Usuário não encontrado")
            
            if user.active:
                raise ValueError("Usuário já ativo")
            
            success: bool = await self.repository.activate(user_id)
            
            # Log activation change
            if success and performed_by_user_id:
                from src.data.repositories.log_user_activation_repository import LogUserActivationRepository
                log_repo = LogUserActivationRepository(self.repository.session)
                await log_repo.log(
                    deactivation_reason=None,
                    activated=True,
                    user_id=user_id.bytes,
                    performed_by_user_id=performed_by_user_id.bytes,
                    performed_by_user_ip_address=user_ip_address or "unknown"
                )

            self.repository.session.commit()
            
            return success
        except Exception as e:
            await ApplicationLogger.log_error(e, reraise=True)
    
    async def find_users(
        self,
        name: Optional[str] = None,
        document: Optional[str] = None,
        email: Optional[str] = None,
        phoneNumber: Optional[str] = None,
        user_type_id: Optional[int] = None,
        active: Optional[bool] = None,
        page: int = 1,
        page_size: int = 10
    ) -> dict:
        """Find users with filters and pagination"""
        try:
            skip: int = (page - 1) * page_size
            models: List[UserModel] = await self.repository.find_by_filters(
                name=name,
                document=document,
                email=email,
                phoneNumber=phoneNumber,
                user_type_id=user_type_id,
                active=active,
                skip=skip,
                limit=page_size
            )
            
            return [UserMapper.model_to_schema(model) for model in models]
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

        password_length: int = len(password)
        
        # Check length
        if password_length < 8:
            raise ValueError("A senha deve conter pelo menos 8 caracteres")
        
        if password_length > 128:
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

    async def _create_address(self, dto: AddressCreate):
        from src.data.models.address_model import AddressModel
        from src.application.mappers.address_mapper import AddressMapper
        from src.data.repositories.address_repository import AddressRepository

        address_repo = AddressRepository(self.repository.session)
        model: AddressModel = AddressMapper.create_to_model(dto)
        saved_model: AddressModel = await address_repo.create(model)

        return AddressMapper.model_to_schema(saved_model)
    
    async def _get_new_student_sequential(self) -> int:
        """Get the latest student sequential"""
        last_sequential: int = await self.repository.get_last_student_sequential()
        new_sequential: int = last_sequential + 1

        return new_sequential
