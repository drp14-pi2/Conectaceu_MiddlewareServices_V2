"""Course mapper"""
from src.data.models.course_model import CourseModel
from src.domain.schemas.course import Course, CourseCreate, CourseUpdate

class CourseMapper:
    @staticmethod
    def model_to_schema(model: CourseModel) -> Course:
        return Course.model_validate(model)

    @staticmethod
    def create_to_model(dto: CourseCreate) -> CourseModel:
        return CourseModel(**dto.model_dump())

    @staticmethod
    def update_model(model: CourseModel, dto: CourseUpdate) -> CourseModel:
        for field, value in dto.model_dump(exclude_none=True).items():
            setattr(model, field, value)
        return model
