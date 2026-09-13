"""Database context"""
from typing import AsyncGenerator, Optional
from sqlalchemy.orm import Session

from src.data.db_context.database import SessionLocal, engine
from src.data.repositories.legal_representative_degree_repository import LegalRepresentativeDegreeRepository
from src.data.repositories.profiles_to_exclude_repository import ProfilesToExcludeRepository
from src.data.repositories.student_absence_justification_repository import StudentAbsenceJustificationRepository
from src.data.repositories.user_repository import UserRepository
from src.data.repositories.address_repository import AddressRepository
from src.data.repositories.course_repository import CourseRepository
from src.data.repositories.course_component_repository import CourseComponentRepository
from src.data.repositories.class_repository import ClassRepository
from src.data.repositories.class_attendance_repository import ClassAttendanceRepository
from src.data.repositories.user_course_repository import UserCourseRepository
from src.data.repositories.document_repository import DocumentRepository
from src.data.repositories.document_type_repository import DocumentTypeRepository
from src.data.repositories.document_validation_repository import DocumentValidationRepository
from src.data.repositories.document_validation_status_type_repository import DocumentValidationStatusTypeRepository
from src.data.repositories.legal_representative_repository import LegalRepresentativeRepository
from src.data.repositories.user_sex_type_repository import UserSexTypeRepository
from src.data.repositories.user_gender_type_repository import UserGenderTypeRepository
from src.data.repositories.user_type_repository import UserTypeRepository
from src.data.repositories.user_password_history_repository import UserPasswordHistoryRepository
from src.data.repositories.shift_type_repository import ShiftTypeRepository
from src.data.repositories.report_type_repository import ReportTypeRepository
from src.data.repositories.enrollment_waiting_list_repository import EnrollmentWaitingListRepository

# Log repositories
from src.data.repositories.log_application_error_repository import LogApplicationErrorRepository
from src.data.repositories.log_broadcast_message_repository import LogBroadcastMessageRepository
from src.data.repositories.log_course_creation_repository import LogCourseCreationRepository
from src.data.repositories.log_document_request_repository import LogDocumentRequestRepository
from src.data.repositories.log_document_validation_repository import LogDocumentValidationRepository
from src.data.repositories.log_report_request_repository import LogReportRequestRepository
from src.data.repositories.log_student_enrollment_repository import LogStudentEnrollmentRepository
from src.data.repositories.log_user_activation_repository import LogUserActivationRepository

from src.data.db_context.base import Base

class DatabaseContext:
    """
    Central database context managing sessions and repositories.
    """
    
    def __init__(self, session: Optional[Session] = None):
        self._session = session
        self._owns_session = session is None
        
        # Business repositories
        self.users = UserRepository(self.session)
        self.addresses = AddressRepository(self.session)
        self.courses = CourseRepository(self.session)
        self.course_components = CourseComponentRepository(self.session)
        self.classes = ClassRepository(self.session)
        self.class_attendances = ClassAttendanceRepository(self.session)
        self.user_courses = UserCourseRepository(self.session)
        self.documents = DocumentRepository(self.session)
        self.document_types = DocumentTypeRepository(self.session)
        self.document_validations = DocumentValidationRepository(self.session)
        self.document_validation_status_types = DocumentValidationStatusTypeRepository(self.session)
        self.legal_representatives = LegalRepresentativeRepository(self.session)
        self.user_sex_types = UserSexTypeRepository(self.session)
        self.user_gender_types = UserGenderTypeRepository(self.session)
        self.user_types = UserTypeRepository(self.session)
        self.password_histories = UserPasswordHistoryRepository(self.session)
        self.shift_types = ShiftTypeRepository(self.session)
        self.report_types = ReportTypeRepository(self.session)
        self.legal_representative_degrees = LegalRepresentativeDegreeRepository(self.session)
        self.profiles_to_exclude = ProfilesToExcludeRepository(self.session)
        self.student_absence_justification = StudentAbsenceJustificationRepository(self.session)
        self.enrollment_waiting_list = EnrollmentWaitingListRepository(self.session)
        
        # Log repositories
        self.log_application_errors = LogApplicationErrorRepository(self.session)
        self.log_broadcast_messages = LogBroadcastMessageRepository(self.session)
        self.log_course_creations = LogCourseCreationRepository(self.session)
        self.log_document_requests = LogDocumentRequestRepository(self.session)
        self.log_document_validations = LogDocumentValidationRepository(self.session)
        self.log_report_requests = LogReportRequestRepository(self.session)
        self.log_student_enrollments = LogStudentEnrollmentRepository(self.session)
        self.log_user_activations = LogUserActivationRepository(self.session)
    
    @property
    def session(self) -> Session:
        """Get or create a database session"""
        if self._session is None:
            self._session = SessionLocal()
        return self._session
    
    async def save_changes(self) -> None:
        """Commit all changes to database"""
        await self.session.commit()
    
    async def rollback(self) -> None:
        """Rollback current transaction"""
        await self.session.rollback()
    
    async def close(self) -> None:
        """Close the session if open"""
        if self._owns_session and self._session:
            self._session.close()
            self._session = None
    
    async def __aenter__(self):
        """Async context manager entry"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if exc_type is not None:
            await self.rollback()
        else:
            await self.save_changes()
        await self.close()


# Dependency for FastAPI
async def get_db_context() -> AsyncGenerator[DatabaseContext, None]:
    """Dependency injection for DatabaseContext"""
    context = DatabaseContext()
    try:
        yield context
    finally:
        await context.close()
