"""Document validation service - business logic for Document Validation entity"""
from typing import List, Optional
from uuid import UUID

from src.application.logging.application_logger import ApplicationLogger
from src.application.mappers.document_validation_mapper import DocumentValidationMapper
from src.data.models.document_model import DocumentModel
from src.data.models.document_validation_model import DocumentValidationModel
from src.data.repositories.document_repository import DocumentRepository
from src.data.repositories.document_validation_repository import DocumentValidationRepository
from src.data.repositories.legal_representative_repository import LegalRepresentativeRepository
from src.application.services.base_service import BaseService
from src.domain.schemas.document_validation import DocumentValidation, DocumentValidationInput
from src.infrastructure.handlers.datetime_handler import DateTimeHandler

class DocumentValidationService(BaseService):
    """Service for Document Validation business logic"""
    
    def __init__(
        self,
        repository: DocumentValidationRepository,
        representative_repo: LegalRepresentativeRepository,
        doc_repo: DocumentRepository
    ):
        super().__init__(repository, 'document_validation', mapper_class=DocumentValidationMapper)
        self.repository = repository
        self.representative_repo = representative_repo
        self.doc_repo = doc_repo
    
    async def create_or_update_validation(
        self, 
        dto: DocumentValidationInput,
        performed_by_user_id: Optional[UUID] = None,
        user_ip_address: Optional[str] = None
    ) -> DocumentValidation:
        """
        Create or update a document validation.
        If validation exists for this document, update it.
        If not, create a new one.
        """
        try:
            # If rejection, a reason must be provided
            if dto.document_validation_status_type_id == 3 and (not dto.rejection_reason or len(dto.rejection_reason) <= 0):
                raise ValueError("Rejeição de documento precisa de uma justificativa")
            
            document_uuid: UUID = dto.document_id
            # Try to find existing validation
            existing_model: DocumentValidationModel | None = await self.repository.get_by_document_id(document_uuid)
            
            if existing_model:
                # Update existing validation
                updated_model: DocumentValidationModel = DocumentValidationModel(
                    document_id=existing_model.document_id,
                    document_validation_status_type_id=dto.document_validation_status_type_id,
                    rejection_reason=dto.rejection_reason
                )
                saved_model: DocumentModel = await self.repository.update(updated_model)
            else:
                # Create new validation
                create_dto: DocumentValidationInput = DocumentValidationInput(
                    document_id=str(document_uuid),
                    document_validation_status_type_id=dto.document_validation_status_type_id
                )
                model: DocumentValidationModel = DocumentValidationMapper.create_to_model(create_dto)
                saved_model = await self.repository.create(model)
            
            # Log validation
            if performed_by_user_id:
                await self._log_validation(dto, document_uuid, performed_by_user_id, user_ip_address)

            self.repository.session.commit()

            # If approved, check if user can be activated
            await self._check_user_activation(dto, document_uuid)

            return DocumentValidationMapper.model_to_schema(saved_model)
        except Exception as e:
            await ApplicationLogger.log_error(e, reraise=True)
    
    async def get_pending_validations(self, skip: int = 0, limit: int = 100) -> List[DocumentValidation]:
        """Get pending document validations"""
        try:
            models = await self.repository.get_pending_validations(skip, limit)
            
            return [DocumentValidationMapper.model_to_schema(model) for model in models]
        except Exception as e:
            await ApplicationLogger.log_error(e, reraise=True)

    # Private methods
    async def _log_validation(
        self,
        dto: DocumentValidationInput,
        document_uuid: UUID,
        performed_by_user_id: UUID,
        user_ip_address: str
    ):
        from src.data.repositories.log_document_validation_repository import LogDocumentValidationRepository

        log_repo = LogDocumentValidationRepository(self.repository.session)
        # Get document owner
        document = await self.doc_repo.get_by_id(document_uuid)
        
        await log_repo.log(
            rejection_reason=dto.rejection_reason,
            activated=(dto.document_validation_status_type_id == 2), # Approved
            user_id=document.user_id if document else document_uuid.bytes,
            performed_by_user_id=performed_by_user_id.bytes,
            performed_user_ip_address=user_ip_address or "unknown"
        )

    async def _check_user_activation(self, dto: DocumentValidationInput, document_uuid: UUID):
        if dto.document_validation_status_type_id == 2:
            from src.data.repositories.user_repository import UserRepository

            user_repo = UserRepository(self.repository.session)
            document: DocumentModel | None = await self.doc_repo.get_by_id(document_uuid)

            if document:
                user_uuid: UUID = UUID(bytes=document.user_id)
                documents: List[DocumentModel] = await self.doc_repo.get_by_user_id(user_uuid)
                # Check if all documents have been approved
                all_approved: bool = True

                for doc in documents:
                    doc_uuid: UUID = UUID(bytes=doc.id)
                    doc_validation: DocumentValidationModel | None = await self.repository.get_by_document_id(doc_uuid)

                    if not doc_validation or doc_validation.document_validation_status_type_id != 2:
                        all_approved = False
                        break

                # Check user age. If minor, check legal representative count
                is_minor: bool = (DateTimeHandler.now().date() - dto.birthdate).days < (18 * 365)

                if is_minor:
                    representative_count = len(await self.representative_repo.get_by_user_id(user_uuid))
                    if representative_count <= 0:
                        all_approved = False
                
                if all_approved:
                    await user_repo.activate(user_uuid)
                    self.repository.session.commit()
