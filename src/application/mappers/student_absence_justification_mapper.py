"""Student absence justification mapper"""
from src.data.models.student_absence_justification_model import StudentAbsenceJustificationModel
from src.domain.schemas.student_absence_justification import (
    StudentAbsenceJustification,
    StudentAbsenceJustificationCreate,
)

class StudentAbsenceJustificationMapper:
    @staticmethod
    def model_to_schema(model: StudentAbsenceJustificationModel) -> StudentAbsenceJustification:
        return StudentAbsenceJustification.model_validate(model)

    @staticmethod
    def create_to_model(dto: StudentAbsenceJustificationCreate) -> StudentAbsenceJustificationModel:
        return StudentAbsenceJustificationModel(**dto.model_dump())
