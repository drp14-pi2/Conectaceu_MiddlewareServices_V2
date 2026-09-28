"""Educational unit mapper"""
from src.data.models.educational_unit_model import EducationalUnitModel
from src.domain.schemas.educational_unit import EducationalUnit, EducationalUnitCreate, EducationalUnitUpdate

class EducationalUnitMapper:
    @staticmethod
    def model_to_schema(model: EducationalUnitModel) -> EducationalUnit:
        return EducationalUnit.model_validate(model)

    @staticmethod
    def create_to_model(dto: EducationalUnitCreate) -> EducationalUnitModel:
        return EducationalUnitModel(**dto.model_dump())

    @staticmethod
    def update_model(model: EducationalUnitModel, dto: EducationalUnitUpdate) -> EducationalUnitModel:
        for field, value in dto.model_dump(exclude_none=True).items():
            setattr(model, field, value)
        return model
