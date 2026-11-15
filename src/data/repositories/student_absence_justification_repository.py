from typing import Optional, List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.data.models.student_absence_justification_model import StudentAbsenceJustificationModel
from src.data.models.document_model import DocumentModel
from src.data.models.document_validation_model import DocumentValidationModel
from src.data.repositories.base.base_repository import BaseRepository

class StudentAbsenceJustificationRepository(BaseRepository):
    def __init__(self, session: AsyncSession):
        super().__init__(session, StudentAbsenceJustificationModel)

    async def get_by_attendance_id(self, attendance_id: UUID) -> Optional[StudentAbsenceJustificationModel]:
        """Gets the justification linked to a specific attendance record."""
        stmt = select(StudentAbsenceJustificationModel).where(StudentAbsenceJustificationModel.class_attendance_id == attendance_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_user_id(self, user_id: UUID, skip: int = 0, limit: int = 100) -> List[StudentAbsenceJustificationModel]:
        """Gets all justifications for a student by joining with the attendance table."""
        from src.data.models.class_attendance_model import ClassAttendanceModel
        stmt = select(StudentAbsenceJustificationModel).join(
            ClassAttendanceModel, StudentAbsenceJustificationModel.class_attendance_id == ClassAttendanceModel.id
        ).where(ClassAttendanceModel.user_id == user_id).offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_justification_status(self, attendance_id: UUID) -> Optional[int]:
        """
        Returns the document_validation_status_type_id for the justification
        linked to this attendance, or:
          - None  → no justification, or justification has no document
        """
        stmt = (
            select(DocumentValidationModel.document_validation_status_type_id)
            .select_from(StudentAbsenceJustificationModel)
            .join(DocumentModel, DocumentModel.id == StudentAbsenceJustificationModel.document_id)
            .join(DocumentValidationModel, DocumentValidationModel.document_id == DocumentModel.id)
            .where(StudentAbsenceJustificationModel.class_attendance_id == attendance_id)
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
