#!/usr/bin/env python
"""
Standalone script to deactivate users who have 3 or more absences
without justifications within the last 7 days.
"""
import sys
import asyncio
from pathlib import Path
from datetime import timedelta
from uuid import UUID
from typing import AsyncGenerator

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Models
from sqlalchemy import select, and_
from src.data.db_context.database import SessionLocal
from src.data.models.user_model import UserModel
from src.data.models.address_model import AddressModel
from src.data.models.course_model import CourseModel
from src.data.models.course_component_model import CourseComponentModel
from src.data.models.class_model import ClassModel
from src.data.models.class_attendance_model import ClassAttendanceModel
from src.data.models.user_course_model import UserCourseModel
from src.data.models.document_model import DocumentModel
from src.data.models.document_type_model import DocumentTypeModel
from src.data.models.document_validation_model import DocumentValidationModel
from src.data.models.document_validation_status_type_model import DocumentValidationStatusTypeModel
from src.data.models.legal_representative_model import LegalRepresentativeModel
from src.data.models.legal_representative_degree_model import LegalRepresentativeDegreeModel
from src.data.models.user_sex_type_model import UserSexTypeModel
from src.data.models.user_gender_type_model import UserGenderTypeModel
from src.data.models.user_type_model import UserTypeModel
from src.data.models.user_password_history_model import UserPasswordHistoryModel
from src.data.models.shift_type_model import ShiftTypeModel
from src.data.models.report_type_model import ReportTypeModel
from src.data.models.profiles_to_exclude_model import ProfilesToExcludeModel
from src.data.models.student_absence_justification_model import StudentAbsenceJustificationModel
from src.data.repositories.enrollment_waiting_list_repository import EnrollmentWaitingListRepository

from src.infrastructure.handlers.datetime_handler import DateTimeHandler
from src.infrastructure.configuration.settings import settings

ABSENCE_DAYS = settings.ABSENCE_DAYS
MIN_CONSECUTIVE_UNJUSTIFIED = settings.MIN_CONSECUTIVE_UNJUSTIFIED  # Deactivate only if X unjustified absences
BATCH_SIZE = settings.BATCH_SIZE


def has_consecutive_unjustified(absences: list, min_count: int = 3) -> bool:
    """
    Check for min_count consecutive unjustified absences in session order.
    A justified absence resets the streak.
    """
    streak = 0
    for absence in absences:
        if getattr(absence, 'justified', False):
            streak = 0
        else:
            streak += 1
            if streak >= min_count:
                return True
    return False


async def stream_users_with_unjustified_absences() -> AsyncGenerator[tuple[UserModel, int], None]:
    """Yield users who have X consecutive unjustified absences."""
    session = SessionLocal()
    try:
        cutoff_date = DateTimeHandler.now() - timedelta(days=ABSENCE_DAYS)
        offset = 0
        
        while True:
            # Get absences by active users, ordered by session date
            stmt = (
                select(ClassAttendanceModel)
                .join(UserModel, ClassAttendanceModel.user_id == UserModel.id)
                .join(ClassModel, ClassAttendanceModel.class_id == ClassModel.id)
                .where(
                    and_(
                        UserModel.active == True,
                        ClassAttendanceModel.attended == False,
                        ClassModel.date < cutoff_date
                    )
                )
                .order_by(ClassAttendanceModel.user_id, ClassModel.date)
                .offset(offset)
                .limit(BATCH_SIZE)
            )
            result = session.execute(stmt)
            absences = result.scalars().all()
            
            if not absences:
                break
            
            # Group by user
            user_absences = {}
            for absence in absences:
                user_id = absence.user_id
                if user_id not in user_absences:
                    user_absences[user_id] = []
                user_absences[user_id].append(absence)
            
            # Check each user for consecutive unjustified absences
            for user_id, user_absence_list in user_absences.items():
                # Mark each absence as justified or not
                for absence in user_absence_list:
                    stmt = select(StudentAbsenceJustificationModel).where(
                        StudentAbsenceJustificationModel.class_attendance_id == absence.id
                    )
                    just_result = session.execute(stmt)
                    justification = just_result.scalar_one_or_none()
                    is_document_valid = False
                    if justification and justification.document_id:
                        stmt = select(DocumentModel).where(
                            and_(
                                DocumentModel.id == justification.document_id,
                                DocumentModel.document_type_id == 7 # Absence justification doc type
                            )
                        )
                        document = session.execute(stmt).scalar_one_or_none()
                        if document:
                            stmt = select(DocumentValidationModel).where(
                                and_(
                                    DocumentValidationModel.document_id == document.id,
                                    DocumentValidationModel.document_validation_status_type_id == 2 # Approved document
                                )
                            )
                            doc_validation = session.execute(stmt).scalar_one_or_none()
                            is_document_valid = doc_validation is not None
                    absence.justified = bool(justification and is_document_valid)
                
                # Check for consecutive streak
                if has_consecutive_unjustified(user_absence_list, MIN_CONSECUTIVE_UNJUSTIFIED):
                    user = session.get(UserModel, user_id)
                    if user:
                        unjustified_count = sum(1 for a in user_absence_list if not a.justified)
                        yield user, unjustified_count
            
            offset += BATCH_SIZE
    finally:
        session.close()


async def process_unjustified_absences():
    """Process and deactivate users with consecutive unjustified absences."""
    deactivated = 0
    skipped = 0
    
    print(f"Looking for users with {MIN_CONSECUTIVE_UNJUSTIFIED}+ consecutive unjustified absences")
    print(f"Absences older than {ABSENCE_DAYS} days\n")
    
    async for user, unjustified_count in stream_users_with_unjustified_absences():
        session = SessionLocal()
        try:
            user_uuid = user.id
            user_name = user.name
            
            # Re-fetch in current session
            local_user = session.get(UserModel, user.id)
            if local_user and local_user.active:
                local_user.active = False
                session.commit()
                deactivated += 1
                print(f"  ✓ Deactivated: {user_name} ({user_uuid}) - {unjustified_count} total unjustified")
            else:
                skipped += 1
                print(f"  - Already inactive: {user_name} ({user_uuid})")
                
        except Exception as e:
            session.rollback()
            print(f"  ✗ Error: {e}")
        finally:
            session.close()
    
    print(f"\nDeactivated: {deactivated} | Skipped: {skipped}")


if __name__ == "__main__":
    asyncio.run(process_unjustified_absences())