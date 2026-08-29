"""Document service - business logic for Document entity"""
from typing import List, Optional
from uuid import UUID, uuid4

from src.application.logging.application_logger import ApplicationLogger
from src.data.models.class_model import ClassModel
from src.data.models.document_model import DocumentModel
from src.data.models.user_course_model import UserCourseModel
from src.data.models.user_model import UserModel
from src.data.repositories.address_repository import AddressRepository
from src.data.repositories.document_repository import DocumentRepository
from src.application.services.base_service import BaseService
from src.application.mappers.dto_to_entity_mapper import DtoToEntityMapper
from src.application.mappers.entity_to_model_mapper import EntityToModelMapper
from src.application.mappers.model_to_entity_mapper import ModelToEntityMapper
from src.application.mappers.entity_to_view_model_mapper import EntityToViewModelMapper
from src.data.repositories.user_repository import UserRepository
from src.domain.constants.document_types import DocumentTypes
from src.domain.dtos.document_dto import DocumentCreateDTO
from src.domain.view_models.document_view_model import DocumentViewModel
from src.infrastructure.handlers.datetime_handler import DateTimeHandler
from src.infrastructure.handlers.format_handler import FormatHandler

class DocumentService(BaseService):
    """Service for Document business logic"""
    
    def __init__(
        self,
        repository: DocumentRepository,
        user_repo: UserRepository,
        address_repo: AddressRepository
    ):
        super().__init__(repository, 'document', mapper_class=ModelToEntityMapper)
        self.repository = repository
        self.user_repo = user_repo
        self.address_repo = address_repo
    
    async def upload_document(self, dto: DocumentCreateDTO) -> DocumentViewModel:
        """Upload a new document"""
        try:
            MAX_SIZE_LIMIT: int = 20_000_000
            fileLength: int = len(dto.base64)
            if fileLength > MAX_SIZE_LIMIT:
                raise ValueError(f'Conteúdo do documento não pode ser maior que {MAX_SIZE_LIMIT / 1_000_000} MB')
            
            if fileLength <= 0:
                raise ValueError('Conteúdo do documento não pode ser vazio')
            
            if DocumentTypes.is_template_type(dto.document_type_id):
                raise ValueError('Este tipo de documento não pode ser salvo')
            
            if not dto.user_id:
                raise ValueError('Documento precisa estar atrelado a um usuário')
            
            user = await self.user_repo.get_by_id(UUID(dto.user_id))
            if not user:
                raise ValueError('Usuário não encontrado')
            
            entity = DtoToEntityMapper.document(dto)
            model = EntityToModelMapper.document(entity)
            student_photo_doc_type_id = 4
            is_user_photo = model.document_type_id == student_photo_doc_type_id;
            existing_document = await self.repository.get_latest_document(model)

            saved_model = None
            if existing_document:
                saved_model = existing_document
                existing_document.base64 = dto.base64
                self.repository.update(existing_document)

                if is_user_photo:
                    existing_student_card = (await self.repository.get_by_type(
                        UUID(bytes=user.id),
                        student_photo_doc_type_id
                    ))[0]
                    existing_student_card.base64 = await self._get_student_card_base64(user, dto.base64)
                    await self.repository.update(existing_student_card)
            else:
                saved_model = await self.repository.create(model)

                if is_user_photo:
                    self._create_student_card(user, dto.base64)

            self._create_pending_validation(model)
            self.repository.session.commit()
            saved_entity = ModelToEntityMapper.document(saved_model)

            return EntityToViewModelMapper.document(saved_entity)
        except Exception as e:
            await ApplicationLogger.log_error(e, reraise=True)
    
    async def get_user_documents(self, user_id: UUID) -> List[DocumentViewModel]:
        """Get all documents for a user"""
        try:
            models = await self.repository.get_by_user_id(user_id)
            entities = [ModelToEntityMapper.document(model) for model in models]
            return [EntityToViewModelMapper.document(entity) for entity in entities]
        except Exception as e:
            await ApplicationLogger.log_error(e, reraise=True)
    
    async def get_document_by_id(
        self, 
        document_id: UUID,
        user_id: UUID,
        user_ip_address: str
    ) -> DocumentViewModel:
        """Get document and log the request"""
        try:
            document: DocumentModel = await self.repository.get_by_id(document_id)
            if not document:
                raise ValueError("Nenhum documento encontrado")
            
            # Log document request
            from src.data.repositories.log_document_request_repository import LogDocumentRequestRepository
            log_repo = LogDocumentRequestRepository(self.repository.session)
            await log_repo.log(
                document_id=document.id,
                user_id=user_id.bytes,
                user_ip_address=user_ip_address
            )

            self.repository.session.commit()
            
            entity = ModelToEntityMapper.document(document)

            return EntityToViewModelMapper.document(entity)
        except Exception as e:
            await ApplicationLogger.log_error(e, reraise=True)
        
    async def get_documents_by_type(
        self,
        user_id: UUID,
        document_type_id: int,
        logged_user_id: Optional[UUID] = None,
        user_ip_address: Optional[str] = None
    ) -> List[DocumentViewModel]:
        """Get a document by type"""
        try:
            documents = await self.repository.get_by_type(user_id, document_type_id)
            if not documents or len(documents) <= 0:
                raise ValueError("Nenhum documento encontrado")
            
            if logged_user_id and user_ip_address:
                for document in documents:
                    # Log document request
                    from src.data.repositories.log_document_request_repository import LogDocumentRequestRepository
                    log_repo = LogDocumentRequestRepository(self.repository.session)
                    await log_repo.log(
                        document_id=document.id,
                        user_id=logged_user_id.bytes,
                        user_ip_address=user_ip_address
                    )

            self.repository.session.commit()
            
            entities = [ModelToEntityMapper.document(model) for model in documents]

            return [EntityToViewModelMapper.document(entity) for entity in entities]
        except Exception as e:
            await ApplicationLogger.log_error(e, reraise=True)

    async def get_management_document_template(
        self,
        document_type_id: int,
        component_id: Optional[UUID],
        month: Optional[int]
    ) -> Optional[dict]:
        try:
            if not DocumentTypes.is_template_type(document_type_id):
                raise ValueError('Tipo de documento inválido')
            
            document_base64: str = ''

            match DocumentTypes(document_type_id):
                case DocumentTypes.HEALTH_CERTIFICATE_TEMPLATE:
                    document_base64 = self._get_health_certificate_template()
                case DocumentTypes.REGISTER_USER_FORM_TEMPLATE:
                    document_base64 = self._get_register_user_form_template()
                case DocumentTypes.ATTENDANCE_LIST_TEMPLATE:
                    if not component_id:
                        raise ValueError('ID Curso do curso inválido')
                    if not month or month <= 0 or month > 12:
                        raise ValueError('Mês inválido')
                    document_base64 = await self._get_attendance_list_template(component_id, month)
                case _:
                    return None
                
            fileName: str = f'arquivo_{str(uuid4()).replace('-', '')}.pdf'

            return {
                'fileName': fileName,
                'base64': document_base64
            }
        except Exception as e:
            await ApplicationLogger.log_error(e, reraise=True)
    
    async def delete_document(self, document_id: UUID) -> bool:
        """Delete a document"""
        try:
            document = await self.repository.get_by_id(document_id)
            if not document:
                raise ValueError("Nenhum documento encontrado")
            
            result = await self.repository.delete(document_id)
            self.repository.session.commit()

            return result
        except Exception as e:
            await ApplicationLogger.log_error(e, reraise=True)

    async def _create_pending_validation(self, document: DocumentModel) -> None:
        """Create pending validation for secretary review"""
        from uuid import uuid4
        from src.domain.entities.document_validation import DocumentValidation
        from src.application.mappers.entity_to_model_mapper import EntityToModelMapper
        from src.data.repositories.document_validation_repository import DocumentValidationRepository
        doc_validation_repo = DocumentValidationRepository(self.repository.session)
        
        validation = DocumentValidation(
            id=uuid4(),
            created_at=DateTimeHandler.now(),
            updated_at=None,
            rejection_reason=None,
            document_validation_status_type_id=1,  # Pending
            document_id=UUID(bytes=document.id)
        )
        validation_model = EntityToModelMapper.document_validation(validation)
        await doc_validation_repo.create(validation_model)

    # PDF rendering
    def _render_to_base64(self, html: str) -> str:
        """Render the HTML as PDF"""
        from src.infrastructure.pdf.pdf_render_service import PdfRenderService

        return PdfRenderService.render_to_base64(html)

    # Student card
    async def _get_student_card_base64(self, user: UserModel, photo_base_64: str) -> str:
        if len(photo_base_64) <= 0:
            raise ValueError('Foto de usuário não pode ser vazia')
        
        card_html = ''
        with open("src/templates/docs/student_card.html", "r", encoding="utf-8") as f:
            card_html = f.read()
        card_html = card_html.replace('${studentSequential}', str(user.student_sequential))
        card_html = card_html.replace('${name}', user.name)
        card_html = card_html.replace('${document}', user.document)
        card_html = card_html.replace('${birthdate}', user.birthdate.strftime("%d/%m/%Y"))
        card_html = card_html.replace('${studentPhotoBase64}', photo_base_64.base64)
        user_address = (await self.address_repo.get_by_user_id(UUID(bytes=user.id)))[0]
        card_html = card_html.replace(
            '${userFullAddress}',
            f'{user_address.street}, {user_address.number} - {user_address.neighborhood}, {FormatHandler.format_zip_code(user_address.zip_code)}' if user_address else ''
        )
        student_phone_number = user.cellphone_number if user.cellphone_number else ''
        card_html = card_html.replace('${userPhoneNumber}', FormatHandler.format_phone(student_phone_number))

        return self._render_to_base64(card_html)
    
    async def _create_student_card(self, user: UserModel, photo_base_64: str) -> DocumentCreateDTO:
        user_id: UUID = UUID(bytes=user.id)
        card = DocumentModel(
            base64=self._get_student_card_base64(user, photo_base_64),
            user_id=str(user_id),
            document_type_id=8,
            is_front=None,
            legal_representative_id=None
        )
        
        doc_entity = DtoToEntityMapper.document(card)
        doc_entity.user_id = user_id
        doc_model = EntityToModelMapper.document(doc_entity)

        await self.repository.create(doc_model)
    
    # Health certificate
    def _get_health_certificate_template(self) -> str:
        """Get the health certificate template"""
        with open('src/templates/docs/health_certificate.html', 'r', encoding='utf-8') as f:
            return self._render_to_base64(f.read())

    # Register user form template
    def _get_register_user_form_template(self) -> str:
        "Get the register user form template"
        with open('src/templates/docs/register_user_form_template.html', 'r', encoding='utf-8') as f:
            return self._render_to_base64(f.read())
    
    # Attendance list template
    def _generate_attendance_list_day_wrappers(self, classes_in_month: list[ClassModel]) -> str:
        WEEKDAYS: list[str] = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]
        result_html: str = ''
        day_wrapper_html: str = '''
<th class="day_wrapper">
    <p>${day}</p>
    <p>${weekDay}</p>
</th>'''

        for class_ in classes_in_month:
            aux_html: str = day_wrapper_html.replace('${day}', class_.date.strftime("%d/%m"))
            aux_html = aux_html.replace('${weekDay}', WEEKDAYS[class_.date.weekday()])
            result_html += aux_html
        
        return result_html

    async def _generate_attendance_list_student_rows(
        self,
        enrollments: list[UserCourseModel],
        classes_count: int
    ) -> str:
        ATTENDANCE_CELL = '<td class="attendance_check"></td>'
        RESULT_CELL = '<td class="attended_count"></td><td class="absence_count"></td>'
        STUDENT_ROW_HTML: str = '''
<tr>
    <td class="student">
        <span class="student_inner_wrapper">
            <span class="student_position">${studentPosition}</span>
            <p class="student_name">${studentName}</p>
        </span>
    </td>
    <td class="eol_check"></td>
    ${attendanceCells}
    ${resultCells}
</tr>'''
        result_html: str = ''
        attendance_cells = ATTENDANCE_CELL * classes_count
        
        count = 1
        for enrollment in enrollments:
            user = await self.user_repo.get_by_id(UUID(bytes=enrollment.user_id))
            if not user:
                continue
            
            row = STUDENT_ROW_HTML.replace('${studentPosition}', str(count))
            row = row.replace('${studentName}', user.name)
            row = row.replace('${attendanceCells}', attendance_cells)
            row = row.replace('${resultCells}', RESULT_CELL)
            result_html += row
            count += 1
        
        return result_html
    
    def _get_schedule_description(self, classes_in_month: list[ClassModel]) -> str:
        """Returns: 'Segunda, Terça, Quarta\n10h00'"""
        WEEKDAYS_FULL = [
            "Segunda", "Terça", "Quarta",
            "Quinta", "Sexta", "Sábado", "Domingo"
        ]
        
        seen = set()
        time = classes_in_month[0].date.strftime("%Hh%M") if classes_in_month else ""
        
        for c in classes_in_month:
            seen.add(c.date.weekday())
        
        sorted_days = sorted(seen)
        day_names = [WEEKDAYS_FULL[d] for d in sorted_days]
        
        return f"{', '.join(day_names)}<br>{time}"

    async def _get_attendance_list_template(self, component_id: UUID, month: int) -> str:
        """Get the attendance list template"""
        if month <= 0:
            raise ValueError('Mês inválido')

        from src.data.models.course_model import CourseModel
        from src.data.models.course_component_model import CourseComponentModel
        from src.data.repositories.user_course_repository import UserCourseRepository
        from src.data.repositories.course_repository import CourseRepository
        from src.data.repositories.course_component_repository import CourseComponentRepository
        from src.data.repositories.class_repository import ClassRepository
        user_course_repo = UserCourseRepository(self.repository.session)
        course_repo = CourseRepository(self.repository.session)
        component_repo = CourseComponentRepository(self.repository.session)
        class_repo = ClassRepository(self.repository.session)

        component: CourseComponentModel = await component_repo.get_by_id(component_id)
        if not component:
            raise ValueError('Componente não existe')
        
        classes_in_month: list[ClassModel] = await class_repo.get_by_component_and_month(component_id, month)
        class_count: int = len(classes_in_month)
        if class_count == 0:
            raise ValueError('Nenhuma aula encontrada para o mês')
        
        course: CourseModel = await course_repo.get_by_id(UUID(bytes=component.course_id))
        if not course:
            raise ValueError('Curso não encontrado')
        
        enrollments: list[UserCourseModel] = await user_course_repo.get_active_by_course_id(UUID(bytes=course.id))
        if len(enrollments) == 0:
            raise ValueError('Nenhuma matricula encontrada para o curso')
        
        educator: UserModel = await self.user_repo.get_by_id(UUID(bytes=course.responsible_educator_1))
        if not educator:
            raise ValueError('Educador responsável não encontrado')

        html = ''
        with open('src/templates/docs/attendance_list_template.html', 'r', encoding='utf-8') as f:
            html = f.read()

        html = html.replace('${responsibleName}', educator.name)
        html = html.replace('${responsibleOccupation}', '')
        html = html.replace('${classCodeOnEol}', '')
        html = html.replace('${componentName}', component.name)
        html = html.replace('${ageGroup}', '')
        html = html.replace('${classTimeDays}', self._get_schedule_description(classes_in_month))
        html = html.replace('${class}', '')
        html = html.replace('${day_wrappers}', self._generate_attendance_list_day_wrappers(classes_in_month))
        html = html.replace('${studentRows}', await self._generate_attendance_list_student_rows(enrollments, class_count))
        
        # testing
        from src.infrastructure.pdf.pdf_render_service import PdfRenderService
        pdf_bytes = PdfRenderService.render_to_bytes(html)
        with open("test.pdf", "wb") as f:
            f.write(pdf_bytes)
        # end of testing
        
        return self._render_to_base64(html)