#!/usr/bin/env python
"""
Standalone script to process profiles_to_exclude entries.
For entries older than X hours, the user's personal data is anonymized.
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
from sqlalchemy import and_, select
from src.data.db_context.database import SessionLocal
from src.data.models.user_model import UserModel
from src.data.models.address_model import AddressModel
from src.data.models.course_model import CourseModel
from src.data.models.course_component_model import CourseComponentModel
from src.data.models.class_model import ClassModel
from src.data.models.class_attendance_model import ClassAttendanceModel
from src.data.models.enrollment_model import EnrollmentModel
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

EXCLUSION_HOURS = settings.EXCLUSION_HOURS
BATCH_SIZE = settings.BATCH_SIZE


async def _stream_exclusions() -> AsyncGenerator[ProfilesToExcludeModel, None]:
    """Yield exclusion entries one batch at a time."""
    session = SessionLocal()
    try:
        cutoff_date = DateTimeHandler.now() - timedelta(hours=EXCLUSION_HOURS)
        offset = 0
        
        while True:
            stmt = (
                select(ProfilesToExcludeModel)
                .where(
                    and_(
                        ProfilesToExcludeModel.created_at < cutoff_date,
                        ProfilesToExcludeModel.processed == False
                    )
                )
                .offset(offset)
                .limit(BATCH_SIZE)
            )
            result = session.execute(stmt)
            batch = result.scalars().all()
            
            if not batch:
                break
            
            for exclusion in batch:
                yield exclusion
            
            offset += BATCH_SIZE
    finally:
        session.close()

def get_anonymized_unique_value(model_id: UUID) -> str:
    return f"ANONYMIZED_{str(model_id).replace('-', '')[:8]}"

async def process_exclusions():
    processed = 0
    
    async for exclusion in _stream_exclusions():
        session = SessionLocal()
        try:
            user_id = exclusion.user_id
            user_uuid = user_id
            
            print(f"Processing user: {user_uuid}")
            
            # Anonymize user
            user = session.get(UserModel, user_id)
            if user:
                user.name = ""
                user.email = None
                user.cellphone_number = None
                user.contact_cellphone_number = None
                user.school = None
                user.password = ""
                user.document = get_anonymized_unique_value(user_id)

            # Unenroll from all active classes
            from src.data.models.enrollment_model import EnrollmentModel

            stmt = select(EnrollmentModel).where(
                EnrollmentModel.user_id == user_id,
                EnrollmentModel.active == True
            )
            active_enrollments = session.execute(stmt).scalars().all()

            enrolled_course_ids = []
            for enrollment in active_enrollments:
                enrollment.active = False
                enrolled_course_ids.append(enrollment.course_id)
            print(f"  - Unenrolled from {len(active_enrollments)} class(es)")

            # Enroll next from waiting list for each freed seat
            from src.data.models.enrollment_waiting_list_model import EnrollmentWaitingListModel

            for course_id in enrolled_course_ids:
                # Get next in line
                stmt = (
                    select(EnrollmentWaitingListModel)
                    .where(EnrollmentWaitingListModel.course_id == course_id)
                    .order_by(EnrollmentWaitingListModel.position)
                    .limit(1)
                )
                next_in_line = session.execute(stmt).scalar_one_or_none()
                
                if next_in_line:
                    # Create enrollment for the waiting user
                    from uuid import uuid4
                    new_enrollment = EnrollmentModel(
                        id=uuid4(),
                        created_at=DateTimeHandler.now(),
                        updated_at=None,
                        active=True,
                        user_id=next_in_line.user_id,
                        class_id=course_id
                    )
                    session.add(new_enrollment)
                    
                    # Remove from waiting list
                    session.delete(next_in_line)
                    
                    print(f"  - Enrolled waiting user for class")

            # Anonymize addresses
            stmt = select(AddressModel).where(AddressModel.user_id == user_id)
            addresses = session.execute(stmt).scalars().all()
            for addr in addresses:
                addr.zip_code = ""
                addr.street = ""
                addr.number = ""
                addr.complement = None
                addr.neighborhood = ""

            # Clear document contents
            stmt = select(DocumentModel).where(DocumentModel.user_id == user_id)
            documents = session.execute(stmt).scalars().all()
            for doc in documents:
                doc.base64 = ""

            # Anonymize legal representatives and their documents
            stmt = select(LegalRepresentativeModel).where(
                LegalRepresentativeModel.user_id == user_id
            )
            representatives = session.execute(stmt).scalars().all()
            for rep in representatives:
                rep.name = ""
                rep.document = ""
                
                stmt = select(DocumentModel).where(
                    DocumentModel.legal_representative_id == rep.id
                )
                rep_docs = session.execute(stmt).scalars().all()
                for doc in rep_docs:
                    doc.base64 = ""

            # Re-fetch the exclusion in the current session
            local_exclusion = session.get(ProfilesToExcludeModel, exclusion.id)
            if local_exclusion:
                local_exclusion.processed = True

            session.commit()
            processed += 1
            print(f"  ✓ Anonymized")
            
        except Exception as e:
            session.rollback()
            print(f"  ✗ Error: {e}")
        finally:
            session.close()
    
    print(f"\nProcessed {processed} exclusion(s) successfully")


if __name__ == "__main__":
    asyncio.run(process_exclusions())
