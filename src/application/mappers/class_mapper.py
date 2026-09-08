"""Class mapper"""
from src.data.models.class_model import ClassModel
from src.domain.schemas.class_ import Class, ClassCreate, ClassUpdate

class ClassMapper:
    @staticmethod
    def model_to_schema(model: ClassModel) -> Class:
        return Class.model_validate(model)

    @staticmethod
    def create_to_model(dto: ClassCreate) -> ClassModel:
        return ClassModel(**dto.model_dump())

    @staticmethod
    def update_model(model: ClassModel, dto: ClassUpdate) -> ClassModel:
        for field, value in dto.model_dump(exclude_none=True).items():
            setattr(model, field, value)
        return model
