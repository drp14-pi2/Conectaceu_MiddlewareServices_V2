"""User course enrollment mapper"""
from src.data.models.enrollment_model import EnrollmentModel
from src.domain.schemas.enrollment import Enrollment, EnrollmentCreate

class EnrollmentMapper:
    @staticmethod
    def model_to_schema(model: EnrollmentModel) -> Enrollment:
        return Enrollment.model_validate(model)

    @staticmethod
    def create_to_model(dto: EnrollmentCreate) -> EnrollmentModel:
        return EnrollmentModel(**dto.model_dump())
