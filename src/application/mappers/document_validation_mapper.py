"""Document validation mapper"""
from src.data.models.document_validation_model import DocumentValidationModel
from src.domain.schemas.document_validation import DocumentValidation, DocumentValidationInput

class DocumentValidationMapper:
    @staticmethod
    def model_to_schema(model: DocumentValidationModel) -> DocumentValidation:
        return DocumentValidation.model_validate(model)

    @staticmethod
    def create_to_model(dto: DocumentValidationInput) -> DocumentValidationModel:
        return DocumentValidationModel(**dto.model_dump())
