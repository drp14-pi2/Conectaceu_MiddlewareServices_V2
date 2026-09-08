"""Legal representative mapper"""
from src.data.models.legal_representative_model import LegalRepresentativeModel
from src.domain.schemas.legal_representative import (
    LegalRepresentative,
    LegalRepresentativeCreate,
    LegalRepresentativeUpdate,
)

class LegalRepresentativeMapper:
    @staticmethod
    def model_to_schema(model: LegalRepresentativeModel) -> LegalRepresentative:
        return LegalRepresentative.model_validate(model)

    @staticmethod
    def create_to_model(dto: LegalRepresentativeCreate) -> LegalRepresentativeModel:
        return LegalRepresentativeModel(**dto.model_dump())

    @staticmethod
    def update_model(model: LegalRepresentativeModel, dto: LegalRepresentativeUpdate) -> LegalRepresentativeModel:
        for field, value in dto.model_dump(exclude_none=True).items():
            setattr(model, field, value)
        return model
