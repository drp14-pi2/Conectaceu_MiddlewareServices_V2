"""Log services - write-only services for all log entities"""
from uuid import UUID
from typing import Optional

from src.data.repositories.log_application_error_repository import LogApplicationErrorRepository
from src.data.repositories.log_broadcast_message_repository import LogBroadcastMessageRepository
from src.data.repositories.log_course_creation_repository import LogCourseCreationRepository
from src.data.repositories.log_document_request_repository import LogDocumentRequestRepository
from src.data.repositories.log_document_validation_repository import LogDocumentValidationRepository
from src.data.repositories.log_report_request_repository import LogReportRequestRepository
from src.data.repositories.log_student_enrollment_repository import LogStudentEnrollmentRepository
from src.data.repositories.log_user_activation_repository import LogUserActivationRepository

class LogApplicationErrorService:
    """Service for logging application errors"""
    
    def __init__(self, repository: LogApplicationErrorRepository):
        self.repository = repository
    
    async def log_error(self, exception: str, stacktrace: str) -> None:
        """Log an application error"""
        await self.repository.log_error(exception, stacktrace)
        self.repository.session.commit()


class LogBroadcastMessageService:
    """Service for logging broadcast messages"""
    
    def __init__(self, repository: LogBroadcastMessageRepository):
        self.repository = repository
    
    async def log_broadcast(
        self,
        message: str,
        document_1_base64: str,
        document_2_base64: str,
        sent_whatsapp: bool,
        sent_email: bool,
        sent_sms: bool,
        user_id: UUID,
        user_ip_address: str
    ) -> None:
        """Log a broadcast message"""
        await self.repository.log_broadcast(
            message=message,
            document_1_base64=document_1_base64,
            document_2_base64=document_2_base64,
            sent_whatsapp=sent_whatsapp,
            sent_email=sent_email,
            sent_sms=sent_sms,
            user_id=user_id.bytes,
            user_ip_address=user_ip_address
        )
        self.repository.session.commit()


class LogCourseCreationService:
    """Service for logging course creation"""
    
    def __init__(self, repository: LogCourseCreationRepository):
        self.repository = repository
    
    async def log_creation(self, user_id: UUID, user_ip_address: str, course_id: UUID) -> None:
        """Log a course creation"""
        await self.repository.log_course_creation(user_id.bytes, user_ip_address, course_id.bytes)
        self.repository.session.commit()


class LogDocumentRequestService:
    """Service for logging document requests"""
    
    def __init__(self, repository: LogDocumentRequestRepository):
        self.repository = repository
    
    async def log_request(self, document_type_id: int, user_id: UUID, user_ip_address: str) -> None:
        """Log a document request"""
        await self.repository.log_document_request(document_type_id, user_id.bytes, user_ip_address)
        self.repository.session.commit()


class LogDocumentValidationService:
    """Service for logging document validations"""
    
    def __init__(self, repository: LogDocumentValidationRepository):
        self.repository = repository
    
    async def log_validation(
        self,
        rejection_reason: Optional[str],
        activated: bool,
        user_id: UUID,
        performed_by_user_id: UUID,
        performed_user_ip_address: str
    ) -> None:
        """Log a document validation"""
        await self.repository.log_validation(
            rejection_reason=rejection_reason,
            activated=activated,
            user_id=user_id.bytes,
            performed_by_user_id=performed_by_user_id.bytes,
            performed_user_ip_address=performed_user_ip_address
        )
        self.repository.session.commit()


class LogReportRequestService:
    """Service for logging report requests"""
    
    def __init__(self, repository: LogReportRequestRepository):
        self.repository = repository
    
    async def log_request(self, report_type_id: int, user_id: UUID, user_ip_address: str) -> None:
        """Log a report request"""
        await self.repository.log_report_request(report_type_id, user_id.bytes, user_ip_address)
        self.repository.session.commit()


class LogStudentEnrollmentService:
    """Service for logging student enrollments"""
    
    def __init__(self, repository: LogStudentEnrollmentRepository):
        self.repository = repository
    
    async def log_enrollment(
        self,
        enrolled: bool,
        user_id: UUID,
        user_ip_address: str,
        course_id: UUID
    ) -> None:
        """Log a student enrollment/unenrollment"""
        await self.repository.log_enrollment(enrolled, user_id.bytes, user_ip_address, course_id.bytes)
        self.repository.session.commit()


class LogUserActivationService:
    """Service for logging user activations"""
    
    def __init__(self, repository: LogUserActivationRepository):
        self.repository = repository
    
    async def log_activation(
        self,
        deactivation_reason: Optional[str],
        activated: bool,
        user_id: UUID,
        performed_by_user_id: UUID,
        performed_by_user_ip_address: str
    ) -> None:
        """Log a user activation/deactivation"""
        await self.repository.log_activation(
            deactivation_reason=deactivation_reason,
            activated=activated,
            user_id=user_id.bytes,
            performed_by_user_id=performed_by_user_id.bytes,
            performed_by_user_ip_address=performed_by_user_ip_address
        )
        self.repository.session.commit()
