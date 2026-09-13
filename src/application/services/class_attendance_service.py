"""Class attendance service - business logic for attendance"""
from datetime import date
from typing import Any, List, Optional
from uuid import UUID, uuid4

from src.application.logging.application_logger import ApplicationLogger
from src.application.mappers.class_attendance_mapper import ClassAttendanceMapper
from src.data.models.class_attendance_model import ClassAttendanceModel
from src.data.models.class_model import ClassModel
from src.data.models.course_component_model import CourseComponentModel
from src.data.models.document_model import DocumentModel
from src.data.models.document_validation_model import DocumentValidationModel
from src.data.models.student_absence_justification_model import StudentAbsenceJustificationModel
from src.data.models.user_course_model import UserCourseModel
from src.data.repositories.class_attendance_repository import ClassAttendanceRepository
from src.data.repositories.class_repository import ClassRepository
from src.data.repositories.course_component_repository import CourseComponentRepository
from src.data.repositories.document_repository import DocumentRepository
from src.data.repositories.student_absence_justification_repository import StudentAbsenceJustificationRepository
from src.data.repositories.user_course_repository import UserCourseRepository
from src.application.services.base_service import BaseService
from src.domain.schemas.class_attendance import BulkAttendanceCreate, ClassAttendanceCreate
from src.domain.schemas.document import DocumentCreate
from src.domain.schemas.student_absence_justification import StudentAbsenceJustificationCreate
from src.infrastructure.handlers.datetime_handler import DateTimeHandler
from src.application.mappers.student_absence_justification_mapper import StudentAbsenceJustificationMapper

class ClassAttendanceService(BaseService):
    """Service for Class Attendance business logic"""
    
    def __init__(
        self, 
        repository: ClassAttendanceRepository,
        user_course_repo: UserCourseRepository,
        class_repo: ClassRepository,
        component_repo: CourseComponentRepository,
        document_repo: DocumentRepository,
        absence_justification_repo: StudentAbsenceJustificationRepository
    ):
        super().__init__(repository, 'class_attendance', mapper_class=ClassAttendanceMapper)
        self.repository = repository
        self.user_course_repo = user_course_repo
        self.class_repo = class_repo
        self.component_repo = component_repo
        self.document_repo = document_repo
        self.absence_justification_repo = absence_justification_repo
    
    async def take_attendance(self, dto: BulkAttendanceCreate) -> dict[str, Any]:
        class_id: UUID = UUID(dto.class_id)
        class_: ClassModel | None = await self.class_repo.get_by_id(class_id)

        if not class_:
            raise ValueError("Aula não encontrada")
        
        if class_.date.date() > DateTimeHandler.now().date():
            raise ValueError("Não é possível registrar chamada antes da data")
        
        # Get the course for this class
        component: CourseComponentModel | None = await self.component_repo.get_by_id(class_.course_component_id)

        if not component:
            raise ValueError("Componente não encontrado")
        
        course_id: UUID = component.course_id
        created: int = 0
        updated: int = 0
        
        for entry in dto.attendances:
            user_id: UUID = UUID(entry.user_id)
            
            # Validate user is enrolled in the course
            enrollment: UserCourseModel | None = await self.user_course_repo.get_by_user_and_course(user_id, course_id)

            if not enrollment or not enrollment.active:
                continue  # Skip users not enrolled in this course
            
            existing_attendance: ClassAttendanceModel | None  = await self.repository.get_by_user_and_class(user_id, class_id)
            
            if existing_attendance:
                existing_attendance.attended = entry.attended
                await self.repository.update(existing_attendance)
                updated += 1
            else:
                new_attendance: ClassAttendanceCreate = ClassAttendanceCreate(
                    id=uuid4(),
                    created_at=DateTimeHandler.now(),
                    updated_at=None,
                    attended=entry.attended,
                    user_id=user_id,
                    class_id=class_id
                )
                model: ClassAttendanceModel = ClassAttendanceMapper.create_to_model(new_attendance)
                await self.repository.create(model)
                created += 1
        
        self.repository.session.commit()
        summary: dict[str, Any] = await self.repository.get_attendance_summary(class_id)
        
        return {
            'class_id': str(class_id),
            'created': created,
            'updated': updated,
            'summary': summary
        }
    
    async def get_class_attendance(self, class_id: UUID) -> dict:
        try:
            """Get attendance for a class"""
            summary: dict[str, Any] = await self.repository.get_attendance_summary(class_id)
            models: List[ClassAttendanceModel] = await self.repository.get_by_class_id(class_id)
            schemas = [ClassAttendanceMapper.model_to_schema(attendance) for attendance in models]
            
            return {
                'class_id': class_id,
                'attendances': schemas,
                'summary': summary
            }
        except Exception as e:
            await ApplicationLogger.log_error(e, reraise=True)
    
    async def get_user_class_attendance(self, user_id: UUID, class_id: UUID) -> dict[str, Any]:
        """Get attendance summary for a user in a class"""
        try:
            return await self.repository.get_user_attendance_summary(user_id, class_id)
        except Exception as e:
            await ApplicationLogger.log_error(e, reraise=True)
    
    async def get_user_classes(
        self,
        user_id: UUID,
        date: Optional[date] = None,
        attended: Optional[bool] = None,
        page: int = 1,
        page_size: int = 10
    ) -> dict:
        """
        Get all classes for a user with optional filters.
        Shows future classes too (with attended = None).
        
        Args:
            user_id: User to get classes for
            date: Optional filter by specific date
            attended: Optional filter by attendance status (None = all, including future)
            page: Page number
            page_size: Items per page
        
        Returns:
            Dict with paginated class list
        """
        try:
            enrollments: List[UserCourseModel] = await self.user_course_repo.get_active_by_user_id(user_id)
            all_classes: List[dict[str, Any]] = []
            
            for enrollment in enrollments:
                course_id: UUID = enrollment.course_id
                components: List[CourseComponentModel] = await self.component_repo.get_by_course_id(course_id)

                for component in components:
                    component_id: UUID = component.id
                    classes: List[ClassModel] = await self.class_repo.get_by_component_id(component_id)

                    for class_ in classes:
                        class_id: UUID = class_.id
                        
                        if date and class_.date.date() != date:
                            continue
                        
                        attendance: ClassAttendanceModel | None = await self.repository.get_by_user_and_class(user_id, class_id)
                        is_past: bool = class_.date.date() < DateTimeHandler.now().date()
                        attendance_status: bool = attendance.attended if attendance else False
                        
                        if attended is not None:
                            if attended and attendance_status is not True:
                                continue

                            if not attended and attendance_status is not False:
                                continue
                        
                        all_classes.append({
                            'class_id': class_id,
                            'date': class_.date,
                            'attended': attendance_status,
                            'is_past': is_past,
                            'is_future': not is_past,
                            'attendance_id': attendance.id if attendance else None
                        })
            
            all_classes.sort(key=lambda c: c['date'], reverse=True)
            skip = (page - 1) * page_size
            
            return all_classes[skip: skip + page_size]
        except Exception as e:
            await ApplicationLogger.log_error(e, reraise=True)

    async def submit_absence_justification(self, attendance_id: UUID, document: DocumentCreate, user_id: UUID) -> dict:
        """
        Student submits a justification document for an absence.
        """
        if user_id != UUID(document.user_id):
            raise ValueError('Você só pode enviar justificativas por si mesmo')

        # Verify the attendance record exists and belongs to this user
        attendance: ClassAttendanceModel | None = await self.repository.get_by_id(attendance_id)

        if not attendance:
            raise ValueError("Chamada não encontrada")
        
        if attendance.user_id != user_id:
            raise ValueError("Esta chamada não pertence a você")
        
        # Verify if the student was present
        if attendance.attended:
            raise ValueError("Não é possível justificar uma chamada já com presença")
        
        # Check if justification already exists
        existing: StudentAbsenceJustificationModel | None = await self.absence_justification_repo.get_by_attendance_id(attendance_id)

        if existing and existing.document_id:
            raise ValueError("Já existe uma justificativa para esta ausência")
        
        # Create the document
        saved_document: DocumentModel = await self._create_document(document);
        document_id: UUID = saved_document.id

        # Create new justification
        saved_justification: StudentAbsenceJustificationModel = await self._create_justification(attendance_id, document_id)
        self.repository.session.commit()
        
        return {
            "message": "Justificativa carregada com sucesso. Aguarde validação.",
            "justification_id": str(saved_justification.id),
            "document_id": str(document_id)
        }

    # Private methods
    async def _create_document(self, document: DocumentCreate):
        from src.application.mappers.document_mapper import DocumentMapper

        doc_model: DocumentModel = DocumentMapper.create_to_model(document)
        saved_doc: DocumentModel = await self.document_repo.create(doc_model)

        # Create document validation
        from src.data.repositories.document_validation_repository import DocumentValidationRepository
        doc_validation_repo: DocumentValidationRepository = DocumentValidationRepository(self.repository.session)
        doc_validation: DocumentValidationModel = DocumentValidationModel(
            id=uuid4(),
            created_at=DateTimeHandler.now(),
            updated_at=None,
            rejection_reason=None,
            document_validation_status_type_id=1,
            document_id=saved_doc.id
        )
        await doc_validation_repo.create(doc_validation)

    async def _create_justification(self, attendance_id: UUID, document_id: UUID) -> StudentAbsenceJustificationModel:
        justification: StudentAbsenceJustificationCreate = StudentAbsenceJustificationCreate(
            id=uuid4(),
            created_at=DateTimeHandler.now(),
            class_attendance_id=attendance_id,
            document_id=document_id
        )
        justification_model: StudentAbsenceJustificationModel = StudentAbsenceJustificationMapper.create_to_model(justification)
        saved_justification: StudentAbsenceJustificationModel = await self.absence_justification_repo.create(justification_model)

        return saved_justification
