"""User service - business logic for User entity"""
import re
from typing import Any, List, Optional
from uuid import UUID, uuid4

from src.application.logging.application_logger import ApplicationLogger
from src.application.mappers.document_mapper import DocumentMapper
from src.application.mappers.user_mapper import UserMapper
from src.application.services.user_password_history_service import UserPasswordHistoryService
from src.data.models.document_model import DocumentModel
from src.data.models.legal_representative_model import LegalRepresentativeModel
from src.data.models.profiles_to_exclude_model import ProfilesToExcludeModel
from src.data.models.educational_unit_model import EducationalUnitModel
from src.data.models.user_model import UserModel
from src.data.repositories.document_repository import DocumentRepository
from src.data.repositories.document_validation_repository import DocumentValidationRepository
from src.data.repositories.legal_representative_repository import LegalRepresentativeRepository
from src.data.repositories.profiles_to_exclude_repository import ProfilesToExcludeRepository
from src.data.repositories.educational_unit_repository import EducationalUnitRepository
from src.data.repositories.user_repository import UserRepository
from src.application.services.base_service import BaseService
from src.domain.schemas.document import DocumentCreate
from src.domain.schemas.legal_representative import LegalRepresentativeCreate
from src.domain.schemas.user import DeactivateUser, User, UserCreate, UserUpdate
from src.infrastructure.handlers.datetime_handler import DateTimeHandler
from src.infrastructure.handlers.format_handler import FormatHandler
from src.infrastructure.handlers.password_hasher import PasswordHasher
from src.domain.schemas.user_password_history import PasswordChange
from src.domain.schemas.address import AddressCreate
from src.data.models.document_validation_model import DocumentValidationModel

class UserService(BaseService):
    """Service for User business logic"""
    
    def __init__(
        self,
        repository: UserRepository,
        password_history_service: UserPasswordHistoryService,
        profiles_to_exclude_repo: ProfilesToExcludeRepository,
        educational_unit_repo: EducationalUnitRepository,
        document_depo: DocumentRepository,
        representative_repo: LegalRepresentativeRepository,
        doc_validation_repo: DocumentValidationRepository
    ):
        super().__init__(repository, 'user', mapper_class=UserMapper)
        self.repository = repository
        self.password_history_service = password_history_service
        self.profiles_to_exclude_repo = profiles_to_exclude_repo
        self.educational_unit_repo = educational_unit_repo
        self.document_repo = document_depo
        self.representative_repo = representative_repo
        self.doc_validation_repo = doc_validation_repo
    
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
            # Blocks administrator user creation
            if dto.user_type_id == 1:
                raise ValueError('Não é permitido criar esse tipo de usuário')

            # Normalize fields
            dto.document = re.sub(r'\D', '', dto.document)
            dto.name = dto.name.title()
            dto.address.street = dto.address.street.title()
            dto.address.neighborhood = dto.address.neighborhood.title()

            if dto.legal_representative_1:
                dto.legal_representative_1.document = re.sub(r'\D', '', dto.legal_representative_1.document)
            
            if dto.legal_representative_2:
                dto.legal_representative_2.document = re.sub(r'\D', '', dto.legal_representative_2.document)

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
            
            if dto.legal_representative_1 and dto.legal_representative_2 and dto.legal_representative_1.document == dto.legal_representative_2.document:
                raise ValueError("Os representantes legais não podem ser os mesmos")
            
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

            is_minor = (DateTimeHandler.now().date() - dto.birthdate).days < 18 * 365

            # Minors must have legal representative
            if is_minor and not dto.legal_representative_1:
                raise ValueError("Menores de idade devem ter pelo menos 1 (um) representante legal")

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

            educational_unit: EducationalUnitModel | None = await self.educational_unit_repo.get_by_id(dto.educational_unit_id)

            if not educational_unit or not educational_unit.active:
                raise ValueError('Polo inválido')
            
            # Save user
            saved_model: UserModel = await self.repository.create(model)
            user_id: UUID = saved_model.id
            
            # Save password history
            await self.password_history_service.add_password_hash_to_history(
                user_id=user_id,
                hashed_password=model.password
            )
            
            # Creates uploaded documents
            async def _create_document(doc_dto: DocumentCreate, user_id: UUID, legal_rep_id: Optional[UUID] = None) -> DocumentModel:
                if len(doc_dto.base64) <= 0:
                    raise ValueError('Conteúdo do documento não pode ser vazio')
                
                id_document_types = [1, 2, 3]

                if doc_dto.document_type_id in id_document_types and doc_dto.is_front is None:
                    raise ValueError('Documentos de identidade precisam estar declarados como frente ou verso')
                
                doc_model = DocumentMapper.create_to_model(doc_dto)
                doc_model.user_id = user_id

                if legal_rep_id:
                    doc_model.legal_representative_id = legal_rep_id

                return await self.document_repo.create(doc_model)
            
            created_documents_to_validate = []
            created_documents_to_validate.append(await _create_document(dto.id_document_front, user_id))
            created_documents_to_validate.append(await _create_document(dto.id_document_back, user_id))
            created_documents_to_validate.append(await _create_document(dto.user_photo, user_id))
            
            if dto.health_certificate:
                created_documents_to_validate.append(await _create_document(dto.health_certificate, user_id))

            # Create legal representatives
            if is_creating_student:
                async def _create_legal_representative(rep_dto: LegalRepresentativeCreate, student_user_id: UUID):
                    rep_model = LegalRepresentativeModel(
                        id=uuid4(),
                        created_at=DateTimeHandler.now(),
                        name = rep_dto.name,
                        document = rep_dto.document,
                        legal_representative_degree_id = rep_dto.legal_representative_degree_id,
                        user_id = student_user_id
                    )
                    saved_rep = await self.representative_repo.create(rep_model)
                    representative_id = saved_rep.id
                    
                    created_documents_to_validate.append(await _create_document(rep_dto.id_document_front, user_id, representative_id))
                    created_documents_to_validate.append(await _create_document(rep_dto.id_document_back, user_id, representative_id))
                    created_documents_to_validate.append(await _create_document(rep_dto.student_registry_authorization, user_id, representative_id))
                    
                    return saved_rep
                
                if dto.legal_representative_1:
                    await _create_legal_representative(dto.legal_representative_1, user_id)
                
                if dto.legal_representative_2:
                    await _create_legal_representative(dto.legal_representative_2, user_id)
            
            # Create Document Validations
            if is_creator_admin_or_secretary:
                await self._auto_approve_documents(created_documents_to_validate)
            else:
                await self._create_pending_validations(created_documents_to_validate)

            # Create Address
            await self._create_address(dto.address, user_id)

            # Create student card
            if is_creating_student:
                student_card = await self._create_student_card(dto, saved_model.id, saved_model.student_sequential)
                await _create_document(student_card, user_id)

            # saves changes
            await self.repository.session.commit()

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
            
            updated_model: UserModel = UserMapper.update_model(model, dto)
            saved_model: UserModel = await self.repository.update(updated_model)
            await self.repository.session.commit()
            
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

            await self.repository.session.commit()
            
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
                id=uuid4(),
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
                user_id=user_id,
                performed_by_user_id=performed_by_user_id,
                performed_by_user_ip_address=user_ip_address or "unknown"
            )

        await self.repository.session.commit()
        
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
                    user_id=user_id,
                    performed_by_user_id=performed_by_user_id,
                    performed_by_user_ip_address=user_ip_address or "unknown"
                )

            await self.repository.session.commit()
            
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
        educational_units_ids: Optional[list[UUID]] = None,
        page: int = 1,
        page_size: int = 10,
    ) -> List[User]:
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
                educational_units_ids=educational_units_ids,
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

    async def _create_address(self, dto: AddressCreate, user_id: UUID):
        from src.data.models.address_model import AddressModel
        from src.application.mappers.address_mapper import AddressMapper
        from src.data.repositories.address_repository import AddressRepository

        address_repo = AddressRepository(self.repository.session)
        model: AddressModel = AddressMapper.create_to_model(dto)
        model.user_id = user_id
        saved_model: AddressModel = await address_repo.create(model)

        return AddressMapper.model_to_schema(saved_model)

    async def _create_student_card(
        self,
        student_dto: UserCreate,
        student_id: UUID,
        student_sequential: int
    ) -> DocumentCreate:
        card_html = ''

        with open("src/templates/docs/student_card.html", "r", encoding="utf-8") as f:
            card_html = f.read()
        
        card_html = card_html.replace('${studentSequential}', str(student_sequential))
        card_html = card_html.replace('${name}', student_dto.name)
        card_html = card_html.replace('${document}', student_dto.document)
        card_html = card_html.replace('${birthdate}', student_dto.birthdate.strftime("%d/%m/%Y"))
        card_html = card_html.replace('${studentPhotoBase64}', student_dto.user_photo.base64)
        card_html = card_html.replace('${userFullAddress}', f'{student_dto.address.street}, {student_dto.address.number} - {student_dto.address.neighborhood}, {FormatHandler.format_zip_code(student_dto.address.zip_code)}')
        student_phone_number = student_dto.cellphone_number if student_dto.cellphone_number else ''
        card_html = card_html.replace('${userPhoneNumber}', FormatHandler.format_phone(student_phone_number))

        from src.infrastructure.pdf.pdf_render_service import PdfRenderService

        return DocumentCreate(
            base64=PdfRenderService.render_to_base64(card_html),
            user_id=student_id,
            document_type_id=8,
            is_front=None,
            legal_representative_id=None
        )
    
    async def _get_new_student_sequential(self) -> int:
        """Get the latest student sequential"""
        last_sequential: int = await self.repository.get_last_student_sequential()
        new_sequential: int = last_sequential + 1

        return new_sequential

    async def _auto_approve_documents(self, documents: list) -> None:
        """Auto-approve documents for admin/secretary created users"""
        from uuid import uuid4
        
        for doc in documents:
            validation = DocumentValidationModel(
                id=uuid4(),
                created_at=DateTimeHandler.now(),
                updated_at=None,
                rejection_reason=None,
                document_validation_status_type_id=2,  # Approved
                document_id=doc.id
            )
            await self.doc_validation_repo.create(validation)

    async def _create_pending_validations(self, documents: list) -> None:
        """Create pending validations for secretary review"""
        from uuid import uuid4
        
        for doc in documents:
            validation = DocumentValidationModel(
                id=uuid4(),
                created_at=DateTimeHandler.now(),
                updated_at=None,
                rejection_reason=None,
                document_validation_status_type_id=1,  # Pending
                document_id=doc.id
            )
            await self.doc_validation_repo.create(validation)
