"""User course enrollment mapper"""
from src.data.models.user_course_model import UserCourseModel
from src.domain.schemas.user_course import UserCourse, UserCourseCreate

class UserCourseMapper:
    @staticmethod
    def model_to_schema(model: UserCourseModel) -> UserCourse:
        return UserCourse.model_validate(model)

    @staticmethod
    def create_to_model(dto: UserCourseCreate) -> UserCourseModel:
        return UserCourseModel(**dto.model_dump())
