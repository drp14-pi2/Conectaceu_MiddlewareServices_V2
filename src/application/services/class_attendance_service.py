"""Class attendance service - business logic for attendance"""
from datetime import date
from typing import Optional
from uuid import UUID

from src.application.logging.application_logger import ApplicationLogger
from src.data.models.document_validation_model import DocumentValidationModel
from src.data.repositories.class_attendance_repository import ClassAttendanceRepository
from src.data.repositories.class_repository import ClassRepository
from src.data.repositories.course_component_repository import CourseComponentRepository
from src.data.repositories.document_repository import DocumentRepository
from src.data.repositories.student_absence_justification_repository import StudentAbsenceJustificationRepository
from src.data.repositories.user_course_repository import UserCourseRepository
from src.application.services.base_service import BaseService
from src.application.mappers.entity_to_model_mapper import EntityToModelMapper
from src.application.mappers.model_to_entity_mapper import ModelToEntityMapper
from src.application.mappers.entity_to_view_model_mapper import EntityToViewModelMapper
from src.domain.dtos.class_attendance_dto import BulkClassAttendanceCreateDTO
from src.domain.dtos.document_dto import DocumentCreateDTO
from src.infrastructure.handlers.datetime_handler import DateTimeHandler

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
        super().__init__(repository, 'class_attendance', mapper_class=ModelToEntityMapper)
        self.repository = repository
        self.user_course_repo = user_course_repo
        self.class_repo = class_repo
        self.component_repo = component_repo
        self.document_repo = document_repo
        self.absence_justification_repo = absence_justification_repo
    
    async def take_attendance(self, dto: BulkClassAttendanceCreateDTO) -> dict:
        class_id = UUID(dto.class_id)
        
        class_ = await self.class_repo.get_by_id(class_id)
        if not class_:
            raise ValueError("Aula não encontrada")
        
        if class_.date.date() > DateTimeHandler.now().date():
            raise ValueError("Não é possível registrar chamada antes da data")
        
        # Get the course for this class
        component = await self.component_repo.get_by_id(UUID(bytes=class_.course_component_id))
        if not component:
            raise ValueError("Componente não encontrado")
        
        course_id = UUID(bytes=component.course_id)
        
        created = 0
        updated = 0
        
        for entry in dto.attendances:
            user_id = UUID(entry.user_id)
            
            # Validate user is enrolled in the course
            enrollment = await self.user_course_repo.get_by_user_and_course(user_id, course_id)
            if not enrollment or not enrollment.active:
                continue  # Skip users not enrolled in this course
            
            existing = await self.repository.get_by_user_and_class(user_id, class_id)
            
            if existing:
                existing.attended = entry.attended
                await self.repository.update(existing)
                updated += 1
            else:
                from uuid import uuid4
                from src.domain.entities.class_attendance import ClassAttendance
                
                attendance = ClassAttendance(
                    id=uuid4(),
                    created_at=DateTimeHandler.now(),
                    updated_at=None,
                    attended=entry.attended,
                    user_id=user_id,
                    class_id=class_id
                )
                model = EntityToModelMapper.class_attendance(attendance)
                await self.repository.create(model)
                created += 1
        
        self.repository.session.commit()
        summary = await self.repository.get_attendance_summary(class_id)
        
        return {
            'class_id': str(class_id),
            'created': created,
            'updated': updated,
            'summary': summary
        }
    
    async def get_class_attendance(self, class_id: UUID) -> dict:
        try:
            """Get attendance for a class"""
            attendances = await self.repository.get_by_class_id(class_id)
            summary = await self.repository.get_attendance_summary(class_id)
            
            entities = [ModelToEntityMapper.class_attendance(a) for a in attendances]
            view_models = [EntityToViewModelMapper.class_attendance(e) for e in entities]
            
            return {
                'class_id': class_id,
                'attendances': view_models,
                'summary': summary
            }
        except Exception as e:
            await ApplicationLogger.log_error(e, reraise=True)
    
    async def get_user_class_attendance(self, user_id: UUID, class_id: UUID) -> dict:
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
            enrollments = await self.user_course_repo.get_active_by_user_id(user_id)
            all_classes = []
            
            for enrollment in enrollments:
                course_id = UUID(bytes=enrollment.course_id)
                components = await self.component_repo.get_by_course_id(course_id)

                for component in components:
                    component_id = UUID(bytes=component.id)
                    classes = await self.class_repo.get_by_component_id(component_id)

                    for class_ in classes:
                        class_id = UUID(bytes=class_.id)
                        
                        if date and class_.date.date() != date:
                            continue
                        
                        attendance = await self.repository.get_by_user_and_class(user_id, class_id)
                        
                        is_past = class_.date.date() < DateTimeHandler.now().date()
                        attendance_status = None
                        
                        if attendance:
                            attendance_status = attendance.attended
                        elif is_past:
                            attendance_status = False
                        
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
                            'attendance_id': UUID(bytes=attendance.id) if attendance else None
                        })
            
            all_classes.sort(key=lambda c: c['date'], reverse=True)
            skip = (page - 1) * page_size
            items = all_classes[skip:skip + page_size]
            
            return {'items': items}
        except Exception as e:
            await ApplicationLogger.log_error(e, reraise=True)

    async def submit_absence_justification(self, attendance_id: UUID, document: DocumentCreateDTO, user_id: UUID) -> dict:
        """
        Student submits a justification document for an absence.
        """
        if user_id != UUID(document.user_id):
            raise ValueError('Você só pode enviar justificativas por si mesmo')

        from uuid import uuid4
        from src.domain.entities.student_absence_justification import StudentAbsenceJustification
        from src.application.mappers.entity_to_model_mapper import EntityToModelMapper
        
        # Verify the attendance record exists and belongs to this user
        attendance = await self.repository.get_by_id(attendance_id)
        if not attendance:
            raise ValueError("Chamada não encontrada")
        
        if UUID(bytes=attendance.user_id) != user_id:
            raise ValueError("Esta chamada não pertence a você")
        
        # Verify the student was actually absent
        if attendance.attended:
            raise ValueError("Não é possível justificar uma chamada já com presença")
        
        # Check if justification already exists
        existing = await self.absence_justification_repo.get_by_attendance_id(attendance_id)
        if existing and existing.document_id:
            raise ValueError("Já existe uma justificativa para esta ausência")
        
        # Create the document
        from src.application.mappers.dto_to_entity_mapper import DtoToEntityMapper
        
        doc_entity = DtoToEntityMapper.document(document)
        doc_entity.user_id = user_id
        doc_model = EntityToModelMapper.document(doc_entity)
        saved_doc = await self.document_repo.create(doc_model)
        document_id = UUID(bytes=saved_doc.id)

        # Create document validation
        from src.data.repositories.document_validation_repository import DocumentValidationRepository
        doc_validation_repo = DocumentValidationRepository(self.repository.session)
        doc_validation = DocumentValidationModel(
            id=uuid4().bytes,
            created_at=DateTimeHandler.now(),
            updated_at=None,
            rejection_reason=None,
            document_validation_status_type_id=1,
            document_id=UUID(bytes=saved_doc.id)
        )
        await doc_validation_repo.create(doc_validation)
        
        # Create new justification
        justification = StudentAbsenceJustification(
            id=uuid4(),
            created_at=DateTimeHandler.now(),
            class_attendance_id=attendance_id,
            document_id=document_id
        )
        
        justification_model = EntityToModelMapper.student_absence_justification(justification)
        saved = await self.absence_justification_repo.create(justification_model)
        self.repository.session.commit()
        
        return {
            "message": "Justificativa carregada com sucesso. Aguarde validação.",
            "justification_id": str(UUID(bytes=saved.id)),
            "document_id": str(document_id)
        }