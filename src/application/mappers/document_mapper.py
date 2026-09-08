"""Document mapper"""
from src.data.models.document_model import DocumentModel
from src.domain.schemas.document import Document, DocumentCreate, DocumentUpdate

class DocumentMapper:
    @staticmethod
    def model_to_schema(model: DocumentModel) -> Document:
        return Document.model_validate(model)

    @staticmethod
    def create_to_model(dto: DocumentCreate) -> DocumentModel:
        return DocumentModel(**dto.model_dump())

    @staticmethod
    def update_model(model: DocumentModel, dto: DocumentUpdate) -> DocumentModel:
        for field, value in dto.model_dump(exclude_none=True).items():
            setattr(model, field, value)
        return model
