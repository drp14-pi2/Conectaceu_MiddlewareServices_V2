"""Legal representative service - business logic for Legal Representative entity"""
from datetime import date
import re
from typing import List
from uuid import UUID

from src.application.logging.application_logger import ApplicationLogger
from src.data.models.legal_representative_model import LegalRepresentativeModel
from src.data.models.user_model import UserModel
from src.data.repositories.document_repository import DocumentRepository
from src.data.repositories.document_validation_repository import DocumentValidationRepository
from src.data.repositories.legal_representative_repository import LegalRepresentativeRepository
from src.application.services.base_service import BaseService
from src.application.mappers.dto_to_entity_mapper import DtoToEntityMapper
from src.application.mappers.entity_to_model_mapper import EntityToModelMapper
from src.application.mappers.model_to_entity_mapper import ModelToEntityMapper
from src.application.mappers.entity_to_view_model_mapper import EntityToViewModelMapper
from src.application.mappers.update_mapper import UpdateMapper
from src.data.repositories.user_repository import UserRepository
from src.domain.dtos.legal_representative_dto import LegalRepresentativeCreateDTO, LegalRepresentativeUpdateDTO
from src.domain.view_models.legal_representative_view_model import LegalRepresentativeViewModel
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
        super().__init__(repository, 'legal_representative', mapper_class=ModelToEntityMapper)
        self.repository = repository
        self.document_repo = document_repo
        self.document_validation_repo = document_validation_repo
        self.user_repo = user_repo
    
    async def create_representative(self, dto: LegalRepresentativeCreateDTO) -> LegalRepresentativeViewModel:
        """Create a new legal representative"""
        try:
            dto.document = re.sub(r'\D', '', dto.document)
            # Check if document already exists for a representative of the same user
            if await self.repository.document_exists_by_user_id(dto.document, UUID(dto.user_id)):
                raise ValueError("Documento já registrado para um representante deste usuário")
            
            uuid_user_id = UUID(dto.user_id)
            existing_representatives_count = len(await self.get_user_representatives(uuid_user_id))

            if existing_representatives_count >= 2:
                raise ValueError("Usuário já possui o limite de 2 representantes legais")
            
            entity = DtoToEntityMapper.legal_representative(dto)
            model = EntityToModelMapper.legal_representative(entity)
            saved_model = await self.repository.create(model)
            self.repository.session.commit()
            saved_entity = ModelToEntityMapper.legal_representative(saved_model)
            return EntityToViewModelMapper.legal_representative(saved_entity)
        except Exception as e:
            await ApplicationLogger.log_error(e, reraise=True)
    
    async def update_representative(
        self,
        representative_id: UUID,
        dto: LegalRepresentativeUpdateDTO
    ) -> LegalRepresentativeViewModel:
        """Update a legal representative"""
        try:
            model = await self.repository.get_by_id(representative_id)
            if not model:
                raise ValueError("Representante não encontrado")
            
            # Check document uniqueness if being updated
            if dto.document:
                dto.document = re.sub(r'\D', '', dto.document)
                exists = await self.repository.document_exists(dto.document, exclude_id=representative_id)
                if exists:
                    raise ValueError("Documento já registrado")
            
            entity = ModelToEntityMapper.legal_representative(model)
            updated_entity = UpdateMapper.legal_representative(entity, dto)
            updated_model = EntityToModelMapper.legal_representative(updated_entity)
            saved_model = await self.repository.update(updated_model)
            self.repository.session.commit()
            saved_entity = ModelToEntityMapper.legal_representative(saved_model)
            return EntityToViewModelMapper.legal_representative(saved_entity)
        except Exception as e:
            await ApplicationLogger.log_error(e, reraise=True)
    
    async def get_user_representatives(self, user_id: UUID) -> List[LegalRepresentativeViewModel]:
        """Get all legal representatives for a user"""
        try:
            models = await self.repository.get_by_user_id(user_id)
            entities = [ModelToEntityMapper.legal_representative(model) for model in models]
            return [EntityToViewModelMapper.legal_representative(entity) for entity in entities]
        except Exception as e:
            await ApplicationLogger.log_error(e, reraise=True)

    async def delete_representative(self, representative_id: UUID) -> bool:
        """Delete a legal representative"""
        try:
            representative: LegalRepresentativeModel = await self.repository.get_by_id(representative_id)
            if await self._can_delete_representative(representative):
                documents = await self.document_repo.get_by_legal_representative_id(representative_id)
                for document in documents:
                    document_validation = await self.document_validation_repo.get_by_document_id(document.id)
                    await self.document_validation_repo.delete(bytes=document_validation.id)
                    await self.document_repo.delete(bytes=document.id)
                await self.repository.delete(representative_id)
                self.repository.session.commit()
                return True
            return False
        except Exception as e:
            await ApplicationLogger.log_error(e, reraise=True)

    async def _can_delete_representative(self, representative: LegalRepresentativeModel) -> bool:
        """Validates if a representative can be deleted"""
        try:
            representative_id = UUID(bytes=representative.user_id)
            user: UserModel = await self.user_repo.get_by_id(representative_id)
            user_id = UUID(bytes=user.id)
            user_representatives_count: int = len(await self.get_user_representatives(user_id))
            is_user_of_age: bool = (DateTimeHandler.now().date() - user.birthdate.date()).days > 17 * 365
            return user_representatives_count > 1 or is_user_of_age
        except Exception as e:
            await ApplicationLogger.log_error(e, reraise=True)