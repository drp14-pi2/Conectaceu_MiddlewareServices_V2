"""Document validation service - business logic for Document Validation entity"""
from typing import List, Optional
from uuid import UUID

from src.application.logging.application_logger import ApplicationLogger
from src.data.models.document_model import DocumentModel
from src.data.repositories.document_validation_repository import DocumentValidationRepository
from src.data.repositories.legal_representative_repository import LegalRepresentativeRepository
from src.application.services.base_service import BaseService
from src.application.mappers.dto_to_entity_mapper import DtoToEntityMapper
from src.application.mappers.entity_to_model_mapper import EntityToModelMapper
from src.application.mappers.model_to_entity_mapper import ModelToEntityMapper
from src.application.mappers.entity_to_view_model_mapper import EntityToViewModelMapper
from src.application.mappers.update_mapper import UpdateMapper
from src.domain.dtos.document_validation_dto import DocumentValidationDTO
from src.domain.view_models.document_validation_view_model import DocumentValidationViewModel
from src.infrastructure.handlers.datetime_handler import DateTimeHandler

class DocumentValidationService(BaseService):
    """Service for Document Validation business logic"""
    
    def __init__(
            self,
            repository: DocumentValidationRepository,
            representative_repo: LegalRepresentativeRepository):
        super().__init__(repository, 'document_validation', mapper_class=ModelToEntityMapper)
        self.repository = repository
        self.representative_repo = representative_repo
    
    async def create_or_update_validation(
        self, 
        dto: DocumentValidationDTO,
        performed_by_user_id: Optional[UUID] = None,
        user_ip_address: Optional[str] = None
    ) -> DocumentValidationViewModel:
        """
        Create or update a document validation.
        If validation exists for this document, update it.
        If not, create a new one.
        """
        try:
            document_uuid = UUID(dto.document_id)
            
            # Try to find existing validation
            existing_model = await self.repository.get_by_document_id(document_uuid)

            # If rejection, a reason must be provided
            if dto.document_validation_status_type_id == 3 and (not dto.rejection_reason or dto.rejection_reason.isspace):
                raise ValueError("Rejeições de documentos precisam de uma justificativa")
            
            if existing_model:
                # Update existing validation
                entity = ModelToEntityMapper.document_validation(existing_model)
                updated_entity = UpdateMapper.document_validation(entity, dto)
                updated_model = EntityToModelMapper.document_validation(updated_entity)
                saved_model = await self.repository.update(updated_model)
            else:
                # Create new validation
                from src.domain.dtos.document_validation_dto import DocumentValidationDTO
                
                create_dto = DocumentValidationDTO(
                    document_id=str(document_uuid),
                    document_validation_status_type_id=dto.document_validation_status_type_id
                )
                
                entity = DtoToEntityMapper.document_validation(create_dto)
                entity.rejection_reason = dto.rejection_reason
                
                model = EntityToModelMapper.document_validation(entity)
                saved_model = await self.repository.create(model)

            from src.data.repositories.document_repository import DocumentRepository
            doc_repo = DocumentRepository(self.repository.session)
            
            # Log validation
            if performed_by_user_id:
                from src.data.repositories.log_document_validation_repository import LogDocumentValidationRepository
                log_repo = LogDocumentValidationRepository(self.repository.session)
                
                # Get document owner
                document = await doc_repo.get_by_id(document_uuid)
                
                await log_repo.log(
                    rejection_reason=dto.rejection_reason,
                    activated=(dto.document_validation_status_type_id == 2),  # Approved
                    user_id=document.user_id if document else document_uuid.bytes,
                    performed_by_user_id=performed_by_user_id.bytes,
                    performed_user_ip_address=user_ip_address or "unknown"
                )
            
            self.repository.session.commit()

            # If approved, check if user can be activated
            if dto.document_validation_status_type_id == 2:
                from src.data.repositories.user_repository import UserRepository
                user_repo = UserRepository(self.repository.session)
                
                document: DocumentModel = await doc_repo.get_by_id(document_uuid)
                if document:
                    user_uuid = UUID(bytes=document.user_id)
                    documents = await doc_repo.get_by_user_id(user_uuid)

                    # Check if all documents have been approved
                    all_approved = True
                    for doc in documents:
                        doc_uuid = UUID(bytes=doc.id)
                        doc_validation = await self.repository.get_by_document_id(doc_uuid)
                        if not doc_validation or doc_validation.document_validation_status_type_id != 2:
                            all_approved = False
                            break

                    # Check user age. If minor, check legal representative count
                    is_minor = (DateTimeHandler.now().date() - dto.birthdate).days < 18 * 365
                    if is_minor:
                        representative_count = len(await self.representative_repo.get_by_user_id(user_uuid))
                        if representative_count <= 0:
                            all_approved = False
                    
                    if all_approved:
                        await user_repo.activate(user_uuid)
                        self.repository.session.commit()
            
            saved_entity = ModelToEntityMapper.document_validation(saved_model)
            return EntityToViewModelMapper.document_validation(saved_entity)
        except Exception as e:
            await ApplicationLogger.log_error(e, reraise=True)
    
    async def get_pending_validations(self, skip: int = 0, limit: int = 100) -> List[DocumentValidationViewModel]:
        """Get pending document validations"""
        try:
            models = await self.repository.get_pending_validations(skip, limit)
            entities = [ModelToEntityMapper.document_validation(model) for model in models]
            return [EntityToViewModelMapper.document_validation(entity) for entity in entities]
        except Exception as e:
            await ApplicationLogger.log_error(e, reraise=True)
    
    async def get_validation_by_document(self, document_id: UUID) -> DocumentValidationViewModel:
        """Get validation for a document"""
        try:
            model = await self.repository.get_by_document_id(document_id)
            if not model:
                raise ValueError("Validation not found for this document")
            
            entity = ModelToEntityMapper.document_validation(model)
            return EntityToViewModelMapper.document_validation(entity)
        except Exception as e:
            await ApplicationLogger.log_error(e, reraise=True)