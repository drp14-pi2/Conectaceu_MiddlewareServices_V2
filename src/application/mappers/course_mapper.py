"""Course mapper"""
from src.data.models.course_model import CourseModel
from src.domain.schemas.course import Course, CourseCreate, CourseList, CourseUpdate
from src.domain.schemas.course_component import CourseComponent

class CourseMapper:
    @staticmethod
    def model_to_schema(model: CourseModel) -> Course:
        return Course.model_validate(model)

    @staticmethod
    def create_to_model(dto: CourseCreate) -> CourseModel:
        return CourseModel(
            name=dto.name,
            total_seat_limit=dto.total_seat_limit,
            workload=dto.workload,
            min_student_age=dto.min_student_age,
            max_student_age=dto.max_student_age,
            shift_type_id=dto.shift_type_id,
            educational_unit_id=dto.educational_unit_id,
            responsible_educator_1=dto.responsible_educator_1,
            responsible_educator_2=dto.responsible_educator_2
        )

    @staticmethod
    def update_model(model: CourseModel, dto: CourseUpdate) -> CourseModel:
        for field, value in dto.model_dump(exclude_none=True).items():
            setattr(model, field, value)
        return model

    @staticmethod
    def view_with_components(model: CourseModel, components: list[CourseComponent]):
        return CourseList(
            name=model.name,
            total_seat_limit=model.total_seat_limit,
            workload=model.workload,
            min_student_age=model.min_student_age,
            max_student_age=model.max_student_age,
            shift_type_id=model.shift_type_id,
            id=model.id,
            active=model.active,
            educational_unit_id=model.educational_unit_id,
            responsible_educator_1=model.responsible_educator_1,
            responsible_educator_2=model.responsible_educator_2,
            components=components
        )
