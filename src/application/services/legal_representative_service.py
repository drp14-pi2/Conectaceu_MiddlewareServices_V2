"""Legal representative service - business logic for Legal Representative entity"""
import re
from typing import List
from uuid import UUID

from src.application.logging.application_logger import ApplicationLogger
from src.application.mappers.legal_representative_mapper import LegalRepresentativeMapper
from src.data.models.document_model import DocumentModel
from src.data.models.legal_representative_model import LegalRepresentativeModel
from src.data.models.user_model import UserModel
from src.data.repositories.document_repository import DocumentRepository
from src.data.repositories.document_validation_repository import DocumentValidationRepository
from src.data.repositories.legal_representative_repository import LegalRepresentativeRepository
from src.application.services.base_service import BaseService
from src.data.repositories.user_repository import UserRepository
from src.domain.schemas.legal_representative import LegalRepresentative, LegalRepresentativeCreate, LegalRepresentativeUpdate
from src.infrastructure.handlers.datetime_handler import DateTimeHandler

class LegalRepresentativeService(BaseService):
    """Service for Legal Representative business logic"""
    
    def __init__(
        self,
        repository: LegalRepresentativeRepository,
        document_repo: DocumentRepository,
        document_validation_repo: DocumentValidationRepository,
        user_repo: UserRepository
    ):
        super().__init__(repository, 'legal_representative', mapper_class=LegalRepresentativeMapper)
        self.repository = repository
        self.document_repo = document_repo
        self.document_validation_repo = document_validation_repo
        self.user_repo = user_repo
    
    async def create_representative(self, dto: LegalRepresentativeCreate) -> LegalRepresentative:
        """Create a new legal representative"""
        try:
            dto.document = re.sub(r'\D', '', dto.document)
            # Check if document already exists for a representative of the same user
            if await self.repository.document_exists_by_user_id(dto.document, UUID(dto.user_id)):
                raise ValueError("Documento já registrado para um representante deste usuário")
            
            uuid_user_id: UUID = UUID(dto.user_id)
            existing_representatives_count: int = len(await self.get_user_representatives(uuid_user_id))

            if existing_representatives_count >= 2:
                raise ValueError("Usuário já possui o limite de 2 representantes legais")
            
            model: LegalRepresentativeModel = LegalRepresentativeMapper.create_to_model(dto)
            saved_model: LegalRepresentativeModel = await self.repository.create(model)
            self.repository.session.commit()
            
            return LegalRepresentativeMapper.model_to_schema(saved_model)
        except Exception as e:
            await ApplicationLogger.log_error(e, reraise=True)
    
    async def update_representative(
        self,
        representative_id: UUID,
        dto: LegalRepresentativeUpdate
    ) -> LegalRepresentative:
        """Update a legal representative"""
        try:
            model: LegalRepresentativeModel | None = await self.repository.get_by_id(representative_id)

            if not model:
                raise ValueError("Representante não encontrado")

            dto.document = re.sub(r'\D', '', dto.document)
            
            # Check document uniqueness
            if dto.document:
                exists: bool = await self.repository.document_exists(dto.document, exclude_id=representative_id)

                if exists:
                    raise ValueError("Documento já registrado para outro usuário")
            
            updated_model: LegalRepresentativeModel = LegalRepresentativeMapper.update_model(dto)
            saved_model: LegalRepresentativeModel = await self.repository.update(updated_model)
            self.repository.session.commit()
            
            return LegalRepresentativeMapper.model_to_schema(saved_model)
        except Exception as e:
            await ApplicationLogger.log_error(e, reraise=True)
    
    async def get_user_representatives(self, user_id: UUID) -> List[LegalRepresentative]:
        """Get all legal representatives for a user"""
        try:
            models = await self.repository.get_by_user_id(user_id)

            return [LegalRepresentativeMapper.model_to_schema(model) for model in models]
        except Exception as e:
            await ApplicationLogger.log_error(e, reraise=True)

    async def delete_representative(self, representative_id: UUID) -> bool:
        """Delete a legal representative"""
        deleted: bool = False;

        try:
            representative: LegalRepresentativeModel | None = await self.repository.get_by_id(representative_id)

            if await self._can_delete_representative(representative):
                documents: List[DocumentModel] = await self.document_repo.get_by_legal_representative_id(representative_id)

                for document in documents:
                    document_validation = await self.document_validation_repo.get_by_document_id(document.id)
                    await self.document_validation_repo.delete(bytes=document_validation.id)
                    await self.document_repo.delete(bytes=document.id)

                await self.repository.delete(representative_id)
                self.repository.session.commit()
                deleted = True
            
            return deleted
        except Exception as e:
            await ApplicationLogger.log_error(e, reraise=True)

    async def _can_delete_representative(self, representative: LegalRepresentativeModel) -> bool:
        """Validates if a representative can be deleted"""
        try:
            user: UserModel = await self.user_repo.get_by_id(UUID(bytes=representative.user_id))
            is_user_of_age: bool = (DateTimeHandler.now().date() - user.birthdate.date()).days > (17 * 365)

            # Check if user is of age
            if is_user_of_age:
                return True;

            # Check if minor user has more than one legal representative
            user_representatives_count: int = len(await self.get_user_representatives(UUID(bytes=user.id)))

            return user_representatives_count > 1
        except Exception as e:
            await ApplicationLogger.log_error(e, reraise=True)
