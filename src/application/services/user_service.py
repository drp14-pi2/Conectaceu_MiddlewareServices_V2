"""User service - business logic for User entity"""
import re
from typing import List, Optional
from uuid import UUID
import bcrypt

from src.application.logging.application_logger import ApplicationLogger
from src.application.services.user_password_history_service import UserPasswordHistoryService
from src.data.models.document_model import DocumentModel
from src.data.repositories.address_repository import AddressRepository
from src.data.repositories.document_repository import DocumentRepository
from src.data.repositories.document_validation_repository import DocumentValidationRepository
from src.data.repositories.legal_representative_repository import LegalRepresentativeRepository
from src.data.repositories.profiles_to_exclude_repository import ProfilesToExcludeRepository
from src.data.repositories.user_repository import UserRepository
from src.application.services.base_service import BaseService
from src.application.mappers.dto_to_entity_mapper import DtoToEntityMapper
from src.application.mappers.entity_to_model_mapper import EntityToModelMapper
from src.application.mappers.model_to_entity_mapper import ModelToEntityMapper
from src.application.mappers.entity_to_view_model_mapper import EntityToViewModelMapper
from src.application.mappers.update_mapper import UpdateMapper
from src.domain.dtos.document_dto import DocumentCreateDTO
from src.domain.dtos.user_dto import DeactivateUserDTO, UserCreateDTO, UserUpdateDTO, PasswordChangeDTO
from src.domain.view_models.user_view_model import StudentUserViewModel, UserViewModel
from src.infrastructure.handlers.datetime_handler import DateTimeHandler
from src.infrastructure.handlers.format_handler import FormatHandler
from src.infrastructure.handlers.password_hasher import PasswordHasher

class UserService(BaseService):
    """Service for User business logic"""
    
    def __init__(
        self,
        repository: UserRepository,
        password_history_service: UserPasswordHistoryService,
        document_repo: DocumentRepository,
        address_repo: AddressRepository,
        legal_rep_repo: LegalRepresentativeRepository,
        doc_validation_repo: DocumentValidationRepository,
        profiles_to_exclude_repo: ProfilesToExcludeRepository
    ):
        super().__init__(repository, 'user', mapper_class=ModelToEntityMapper)
        self.repository = repository
        self.password_history_service = password_history_service
        self.document_repo = document_repo
        self.address_repo = address_repo
        self.legal_rep_repo = legal_rep_repo
        self.doc_validation_repo = doc_validation_repo
        self.profiles_to_exclude_repo = profiles_to_exclude_repo
    
    async def create_user(
        self, 
        dto: UserCreateDTO, 
        created_by_user_id: Optional[UUID] = None
    ) -> UserViewModel:
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
            
            # Validate passwords
            if dto.password != dto.confirm_password:
                raise ValueError("As senhas são diferentes")
            self._validate_password(dto.password)

            # Hash passwords
            dto.password = PasswordHasher.hash_password(dto.password)
            dto.confirm_password = ''

            # Check if document already exists
            existing = await self.repository.get_by_document(dto.document)
            if existing:
                raise ValueError("Documento pertence a outra pessoa")
            
            # Check if e-mail already exists
            if dto.email:
                existing_email = await self.repository.get_by_email(dto.email)
                if existing_email:
                    raise ValueError("E-mail pertence a outra pessoa")
            
            # Determine creation path
            is_public = created_by_user_id is None
            
            # Validate creator
            if is_public:
                is_creator_admin_or_secretary = False
            else:
                creator = await self.repository.get_by_id(created_by_user_id)
                if not creator:
                    raise ValueError("Usuário criador não encontrado")
                
                if not creator.active:
                    raise ValueError("Usuário criador não está ativo")
                
                # Only Admin (1) and Secretary (2) can create users
                if creator.user_type_id not in [1, 2]:
                    raise ValueError("Este usuário não pode criar outros usuários")
                
                is_creator_admin_or_secretary = True
            # Create User
            entity = DtoToEntityMapper.user(dto)
            is_creating_student = entity.user_type_id == 5

            if entity.email != '' and not is_creator_admin_or_secretary:
                entity.email_verified = False

            if is_creating_student:
                entity.student_sequential = await self._get_new_student_sequential()
            
            # Set user status based on creator role
            is_minor = (DateTimeHandler.now().date() - dto.birthdate).days < 18 * 365
            
            if is_creator_admin_or_secretary and not is_minor:
                entity.active = True
            else:
                entity.active = False
            
            # Save user
            model = EntityToModelMapper.user(entity)
            saved_model = await self.repository.create(model)
            user_id = UUID(bytes=saved_model.id)
            
            # Save password history
            await self.password_history_service.add_password_hash_to_history(
                user_id=user_id,
                hashed_password=entity.password
            )
            
            # ========== Create Address ==========
            address_entity = DtoToEntityMapper.address(dto.address)
            address_entity.user_id = user_id
            address_model = EntityToModelMapper.address(address_entity)
            await self.address_repo.create(address_model)

            self.repository.session.commit()
            
            # ========== Return ViewModel ==========
            saved_entity = ModelToEntityMapper.user(saved_model)

            return EntityToViewModelMapper.user(saved_entity)
        except Exception as e:
            await ApplicationLogger.log_error(e, reraise=True)
    
    async def update_user(self, user_id: UUID, dto: UserUpdateDTO) -> UserViewModel:
        """Update user with business validation"""
        try:
            model = await self.repository.get_by_id(user_id)
            if not model:
                raise ValueError("Usuário não encontrado")
            
            # Check email uniqueness if being updated
            if dto.email:
                existing = await self.repository.get_by_email(dto.email)
                if existing and existing.id != model.id:
                    raise ValueError("E-mail já registrado")
            
            # Convert to entity and apply updates
            entity = ModelToEntityMapper.user(model)
            updated_entity = UpdateMapper.user(entity, dto)
            
            # Save changes
            updated_model = EntityToModelMapper.user(updated_entity)
            saved_model = await self.repository.update(updated_model)

            # Commit the transaction
            self.repository.session.commit()
            
            saved_entity = ModelToEntityMapper.user(saved_model)
            
            return EntityToViewModelMapper.user(saved_entity)
        except Exception as e:
            await ApplicationLogger.log_error(e, reraise=True)
    
    async def change_password(self, user_id: UUID, dto: PasswordChangeDTO) -> bool:
        """Change user password with validation"""
        try:
            user = await self.repository.get_by_id(user_id)
            if not user:
                raise ValueError("Usuário não encontrado")
            
            # Verify current password
            if not self._verify_password(dto.current_password, user.password):
                raise ValueError("Senha atual incorreta")
            
            # Validate new password against history
            validation = await self.password_history_service.validate_password_change(
                user_id=user_id,
                new_plain_password=dto.new_password,
                history_check_count=5
            )
            
            if not validation['valid']:
                raise ValueError(validation['reason'])
            
            # Hash and update password
            hashed_password = self._hash_password(dto.new_password)
            success = await self.repository.update_password(user_id, hashed_password)

            if success:
                # Add to password history
                await self.password_history_service.add_password_hash_to_history(
                    user_id=user_id,
                    hashed_password=hashed_password
                )

            # Commit the transaction
            self.repository.session.commit()
            
            return success
        except Exception as e:
            await ApplicationLogger.log_error(e, reraise=True)
    
    async def deactivate_user(
        self,
        user_id: UUID,
        dto: DeactivateUserDTO,
        performed_by_user_id: Optional[UUID] = None,
        user_ip_address: Optional[str] = None
    ) -> bool:
        """Deactivate user account and add to exclusion list"""
        user = await self.repository.get_by_id(user_id)
        if not user:
            raise ValueError("Usuário não encontrado")
        
        if not user.active:
            raise ValueError("Conta de usuário já desativada")
        
        # Deactivate user
        result = await self.repository.deactivate(user_id)
        
        # Add to profiles to exclude
        if result:
            from uuid import uuid4
            from src.domain.entities.profiles_to_exclude import ProfilesToExclude
            from src.application.mappers.entity_to_model_mapper import EntityToModelMapper
            
            exclusion = ProfilesToExclude(
                id=uuid4(),
                created_at=DateTimeHandler.now(),
                user_id=user_id,
                processed=False
            )
            
            exclusion_model = EntityToModelMapper.profiles_to_exclude(exclusion)
            await self.profiles_to_exclude_repo.create(exclusion_model)
        
        # Log activation change
        if result and performed_by_user_id:
            from src.data.repositories.log_user_activation_repository import LogUserActivationRepository
            log_repo = LogUserActivationRepository(self.repository.session)
            await log_repo.log(
                deactivation_reason=dto.reason,
                activated=False,
                user_id=user_id.bytes,
                performed_by_user_id=performed_by_user_id.bytes,
                performed_by_user_ip_address=user_ip_address or "unknown"
            )

        # Commit the transaction
        self.repository.session.commit()
        
        return result
        
    async def activate_user(
        self, 
        user_id: UUID,
        performed_by_user_id: Optional[UUID] = None,
        user_ip_address: Optional[str] = None
    ) -> bool:
        """Activate user account"""
        try:
            user = await self.repository.get_by_id(user_id)
            if not user:
                raise ValueError("Usuário não encontrado")
            
            if user.active:
                raise ValueError("Usuário já ativo")
            
            result = await self.repository.activate(user_id)
            
            # Log activation change
            if result and performed_by_user_id:
                from src.data.repositories.log_user_activation_repository import LogUserActivationRepository
                log_repo = LogUserActivationRepository(self.repository.session)
                await log_repo.log(
                    deactivation_reason=None,
                    activated=True,
                    user_id=user_id.bytes,
                    performed_by_user_id=performed_by_user_id.bytes,
                    performed_by_user_ip_address=user_ip_address or "unknown"
                )

            # Commit the transaction
            self.repository.session.commit()
            
            return result
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
            skip = (page - 1) * page_size
            
            models = await self.repository.find_by_filters(
                name=name,
                document=document,
                email=email,
                phoneNumber=phoneNumber,
                user_type_id=user_type_id,
                active=active,
                skip=skip,
                limit=page_size
            )
            
            total = await self.repository.count({
                'active': active,
                'user_type_id': user_type_id
            })
            
            entities = [ModelToEntityMapper.user(model) for model in models]
            view_models = [EntityToViewModelMapper.user(entity) for entity in entities]
            
            return view_models
        except Exception as e:
            await ApplicationLogger.log_error(e, reraise=True)
    
    async def find_students(
        self,
        name: Optional[str] = None,
        document: Optional[str] = None,
        email: Optional[str] = None,
        phoneNumber: Optional[str] = None,
        active: Optional[bool] = None,
        page: int = 1,
        page_size: int = 10
    ) -> List[StudentUserViewModel]:
        """Find students with all related data"""
        try:
            skip = (page - 1) * page_size
            
            # Get students
            models = await self.repository.find_by_filters(
                name=name,
                document=document,
                email=email,
                phoneNumber=phoneNumber,
                user_type_id=5,
                active=active,
                skip=skip,
                limit=page_size
            )
            
            total = await self.repository.count({
                'active': active,
                'user_type_id': 5
            })
            
            # Build student items with all related data
            items = []
            for model in models:
                user_id = UUID(bytes=model.id)
                student = await self._build_student_view_model(user_id, model)
                items.append(student)
            
            return items
        except Exception as e:
            await ApplicationLogger.log_error(e, reraise=True)
    
    def _verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(
            plain_password.encode('utf-8'),
            hashed_password.encode('utf-8')
        )
    
    async def _save_password_history(self, user_id: bytes, hashed_password: str) -> None:
        """Save password to history"""
        from src.domain.entities.user_password_history import UserPasswordHistory
        from uuid import uuid4
        
        history = UserPasswordHistory(
            id=uuid4(),
            created_at=DateTimeHandler.now(),
            password=hashed_password,
            user_id=user_id
        )
        
        history_model = EntityToModelMapper.user_password_history(history)
        await self.password_history_service.add_password_hash_to_history(history_model)

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

    async def _build_student_view_model(self, user_id: UUID, user_model) -> StudentUserViewModel:
        """Build complete student view model with all related data"""
        from src.application.mappers.model_to_entity_mapper import ModelToEntityMapper
        from src.application.mappers.entity_to_view_model_mapper import EntityToViewModelMapper
        
        # Basic user data
        user_entity = ModelToEntityMapper.user(user_model)
        user_dict = EntityToViewModelMapper.user(user_entity).model_dump()
        
        # Get address
        address_models = await self.address_repo.get_by_user_id(user_id)
        address = None
        if address_models:
            address_entity = ModelToEntityMapper.address(address_models[0])
            address = EntityToViewModelMapper.address(address_entity).model_dump()
        
        # Get documents by type
        documents = await self.document_repo.get_by_user_id(user_id)
        
        id_document_front = None
        id_document_back = None
        user_photo = None
        health_certificate = None
        
        for doc in documents:
            doc_entity = ModelToEntityMapper.document(doc)
            doc_vm = EntityToViewModelMapper.document(doc_entity).model_dump()
            
            # ID Document Front
            if doc.document_type_id == 2 and doc.is_front:
                id_document_front = doc_vm
            # ID Document Back
            elif doc.document_type_id == 2 and not doc.is_front:
                id_document_back = doc_vm
            # User Photo
            elif doc.document_type_id == 4:
                user_photo = doc_vm
            # Health Certificate
            elif doc.document_type_id == 6:
                health_certificate = doc_vm
        
        # Get legal representatives
        legal_reps = await self.legal_rep_repo.get_by_user_id(user_id)
        
        legal_representative_1 = None
        legal_representative_2 = None
        
        if len(legal_reps) > 0:
            rep_entity = ModelToEntityMapper.legal_representative(legal_reps[0])
            legal_representative_1 = EntityToViewModelMapper.legal_representative(rep_entity).model_dump()
        
        if len(legal_reps) > 1:
            rep_entity = ModelToEntityMapper.legal_representative(legal_reps[1])
            legal_representative_2 = EntityToViewModelMapper.legal_representative(rep_entity).model_dump()
        
        return StudentUserViewModel(
            **user_dict,
            id_document_front=id_document_front,
            id_document_back=id_document_back,
            user_photo=user_photo,
            health_certificate=health_certificate,
            address=address,
            legal_representative_1=legal_representative_1,
            legal_representative_2=legal_representative_2
        )

    async def _auto_approve_documents(self, documents: list) -> None:
        """Auto-approve documents for admin/secretary created users"""
        from uuid import uuid4
        from src.domain.entities.document_validation import DocumentValidation
        from src.application.mappers.entity_to_model_mapper import EntityToModelMapper
        
        for doc in documents:
            validation = DocumentValidation(
                id=uuid4(),
                created_at=DateTimeHandler.now(),
                updated_at=None,
                rejection_reason=None,
                document_validation_status_type_id=2,  # Approved
                document_id=UUID(bytes=doc.id)
            )
            validation_model = EntityToModelMapper.document_validation(validation)
            await self.doc_validation_repo.create(validation_model)

    async def _create_pending_validations(self, documents: list) -> None:
        """Create pending validations for secretary review"""
        from uuid import uuid4
        from src.domain.entities.document_validation import DocumentValidation
        from src.application.mappers.entity_to_model_mapper import EntityToModelMapper
        
        for doc in documents:
            validation = DocumentValidation(
                id=uuid4(),
                created_at=DateTimeHandler.now(),
                updated_at=None,
                rejection_reason=None,
                document_validation_status_type_id=1,  # Pending
                document_id=UUID(bytes=doc.id)
            )
            validation_model = EntityToModelMapper.document_validation(validation)
            await self.doc_validation_repo.create(validation_model)
    
    async def _get_new_student_sequential(self) -> int:
        """Get the latest student sequential"""
        last_sequential = await self.repository.get_last_student_sequential()
        new_sequential = last_sequential + 1
        return new_sequential