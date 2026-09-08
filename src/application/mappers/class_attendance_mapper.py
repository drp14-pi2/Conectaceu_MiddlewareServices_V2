"""Class attendance mapper"""
from src.data.models.class_attendance_model import ClassAttendanceModel
from src.domain.schemas.class_attendance import ClassAttendance, AttendanceUpdate, ClassAttendanceCreate

class ClassAttendanceMapper:
    @staticmethod
    def model_to_schema(model: ClassAttendanceModel) -> ClassAttendance:
        return ClassAttendance.model_validate(model)

    @staticmethod
    def create_to_model(dto: ClassAttendanceCreate) -> ClassAttendanceModel:
        return ClassAttendanceModel(**dto.model_dump())

    @staticmethod
    def update_model(model: ClassAttendanceModel, dto: AttendanceUpdate) -> ClassAttendanceModel:
        for field, value in dto.model_dump(exclude_none=True).items():
            setattr(model, field, value)
        return model
