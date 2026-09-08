"""Course component mapper"""
from src.data.models.course_component_model import CourseComponentModel
from src.domain.schemas.course_component import (
    CourseComponent,
    CourseComponentCreate,
    CourseComponentUpdate,
)

class CourseComponentMapper:
    @staticmethod
    def model_to_schema(model: CourseComponentModel) -> CourseComponent:
        return CourseComponent.model_validate(model)

    @staticmethod
    def create_to_model(dto: CourseComponentCreate) -> CourseComponentModel:
        return CourseComponentModel(**dto.model_dump())

    @staticmethod
    def update_model(model: CourseComponentModel, dto: CourseComponentUpdate) -> CourseComponentModel:
        for field, value in dto.model_dump(exclude_none=True).items():
            setattr(model, field, value)
        return model
