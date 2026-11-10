"""Document service - business logic for Document entity"""
from datetime import date
import re
from typing import List, Optional
from uuid import UUID, uuid4

from src.application.logging.application_logger import ApplicationLogger
from src.application.mappers.document_mapper import DocumentMapper
from src.data.models.class_model import ClassModel
from src.data.models.document_model import DocumentModel
from src.data.models.document_validation_model import DocumentValidationModel
from src.data.models.enrollment_model import EnrollmentModel
from src.data.models.user_model import UserModel
from src.data.repositories.address_repository import AddressRepository
from src.data.repositories.document_repository import DocumentRepository
from src.application.services.base_service import BaseService
from src.data.repositories.document_type_repository import DocumentTypeRepository
from src.data.repositories.legal_representative_degree_repository import LegalRepresentativeDegreeRepository
from src.data.repositories.legal_representative_repository import LegalRepresentativeRepository
from src.data.repositories.user_gender_type_repository import UserGenderTypeRepository
from src.data.repositories.user_repository import UserRepository
from src.data.repositories.user_sex_type_repository import UserSexTypeRepository
from src.domain.constants.document_types import DocumentTypes
from src.domain.schemas.document import Document, DocumentCreate
from src.infrastructure.configuration.settings import settings
from src.infrastructure.handlers.datetime_handler import DateTimeHandler
from src.infrastructure.handlers.format_handler import FormatHandler
from src.data.repositories.log_document_request_repository import LogDocumentRequestRepository
from src.infrastructure.pdf.pdf_render_service import PdfRenderService

class DocumentService(BaseService):
    """Service for Document business logic"""
    
    def __init__(
        self,
        repository: DocumentRepository,
        user_repo: UserRepository,
        address_repo: AddressRepository,
        log_doc_request_repo: LogDocumentRequestRepository,
        representative_repo: LegalRepresentativeRepository,
        sex_type_repo: UserSexTypeRepository,
        gender_type_repo: UserGenderTypeRepository,
        degree_repo: LegalRepresentativeDegreeRepository,
        document_type_repo: DocumentTypeRepository
    ):
        super().__init__(repository, 'document', mapper_class=DocumentMapper)
        self.repository = repository
        self.user_repo = user_repo
        self.address_repo = address_repo
        self.log_doc_request_repo = log_doc_request_repo
        self.representative_repo = representative_repo
        self.sex_type_repo = sex_type_repo
        self.gender_type_repo = gender_type_repo
        self.degree_repo = degree_repo
        self.document_type_repo = document_type_repo
    
    async def upload_document(self, dto: DocumentCreate) -> Document:
        """Upload a new document"""
        try:
            MAX_SIZE_LIMIT: int = 16_000_000
            fileLength: int = len(dto.base64)
            if fileLength > MAX_SIZE_LIMIT:
                raise ValueError(f'Conteúdo do documento não pode ser maior que {MAX_SIZE_LIMIT / 1_000_000} MB')
            
            if fileLength <= 0:
                raise ValueError('Conteúdo do documento não pode ser vazio')
            
            if DocumentTypes.is_template_type(dto.document_type_id):
                raise ValueError('Este tipo de documento não pode ser salvo')
            
            if not dto.user_id:
                raise ValueError('Documento precisa estar atrelado a um usuário')
            
            user = await self.user_repo.get_by_id(dto.user_id)
            if not user:
                raise ValueError('Usuário não encontrado')
            
            model: DocumentModel = DocumentMapper.create_to_model(dto)
            STUDENT_PHOTO_DOC_TYPE_ID: int = 4
            is_user_photo: bool = model.document_type_id == STUDENT_PHOTO_DOC_TYPE_ID;
            existing_document: DocumentModel | None = await self.repository.get_latest_document(model)
            saved_model: DocumentModel | None = None

            if existing_document:
                saved_model = existing_document
                existing_document.base64 = dto.base64
                await self.repository.update(existing_document)

                if is_user_photo:
                    existing_student_card: DocumentModel = (await self.repository.get_by_type(
                        user.id,
                        [8] # student card
                    ))[0]
                    existing_student_card.base64 = await self._get_student_card_base64(user, dto.base64)
                    await self.repository.update(existing_student_card)
            else:
                saved_model = await self.repository.create(model)

                if is_user_photo:
                    await self._create_student_card(user, dto.base64)

                await self._create_pending_validation(model)

            await self.repository.session.commit()

            return DocumentMapper.model_to_schema(saved_model)
        except Exception as e:
            await ApplicationLogger.log_error(e, reraise=True)
    
    async def get_user_documents(self, user_id: UUID) -> List[Document]:
        """Get all documents for a user"""
        try:
            models: List[DocumentModel] = await self.repository.get_by_user_id(user_id)
            
            return [DocumentMapper.model_to_schema(model) for model in models]
        except Exception as e:
            await ApplicationLogger.log_error(e, reraise=True)
    
    async def get_document_by_id(
        self, 
        document_id: UUID,
        user_id: UUID,
        user_ip_address: str
    ) -> Document:
        """Get document and log the request"""
        try:
            user: UserModel | None = await self.user_repo.get_by_id(user_id)

            if not user:
                raise ValueError('Usuário não encontrado')

            document_requests_timeout_minutes: int = settings.DOCUMENT_REQUESTS_TIMEOUT_MINUTES

            # Validates student document request amount
            if user.user_type_id == 5 and await self.log_doc_request_repo.has_exceeded_requests(
                minutes=document_requests_timeout_minutes,
                max_requests=settings.MAX_DOCUMENT_REQUESTS,
                user_id=user_id
            ):
                raise ValueError(f"Quantidade de pedidos de documentos excedida. Tente novamente depois de {document_requests_timeout_minutes} minutos")
            
            document: DocumentModel = await self.repository.get_by_id(document_id)

            if not document:
                raise ValueError("Nenhum documento encontrado")
            
            # Log document request
            await self.log_doc_request_repo.log(
                document_id=document.id,
                user_id=user_id,
                user_ip_address=user_ip_address
            )
            await self.repository.session.commit()

            return DocumentMapper.model_to_schema(document);
        except Exception as e:
            await ApplicationLogger.log_error(e, reraise=True)
        
    async def get_documents_by_type(
        self,
        user_id: UUID,
        document_type_id: int,
        logged_user_id: Optional[UUID] = None,
        user_ip_address: Optional[str] = None
    ) -> List[Document]:
        """Get a document by type"""
        try:
            user: UserModel | None = await self.user_repo.get_by_id(user_id)

            if not user:
                raise ValueError('Usuário não encontrado')

            document_requests_timeout_minutes: int = settings.DOCUMENT_REQUESTS_TIMEOUT_MINUTES

            # Validates student document request amount
            if user.user_type_id == 5 and await self.log_doc_request_repo.has_exceeded_requests(
                minutes=document_requests_timeout_minutes,
                max_requests=settings.MAX_DOCUMENT_REQUESTS,
                user_id=user_id
            ):
                raise ValueError(f"Quantidade de pedidos de documentos excedida. Tente novamente depois de {document_requests_timeout_minutes} minutos")

            models = await self.repository.get_by_type(user_id, [document_type_id])

            if not models or len(models) <= 0:
                raise ValueError("Nenhum documento encontrado")
            
            if logged_user_id and user_ip_address:
                for model in models:
                    # Log document request
                    from src.data.repositories.log_document_request_repository import LogDocumentRequestRepository
                    log_repo = LogDocumentRequestRepository(self.repository.session)
                    await log_repo.log(
                        document_id=model.id,
                        user_id=logged_user_id,
                        user_ip_address=user_ip_address
                    )

            await self.repository.session.commit()

            return [DocumentMapper.model_to_schema(model) for model in models]
        except Exception as e:
            await ApplicationLogger.log_error(e, reraise=True)

    async def get_user_identity_document(self, user_id: UUID) -> list[Document]:
        try:
            user: UserModel | None = await self.user_repo.get_by_id(user_id)

            if not user:
                raise ValueError('Usuário não encontrado')

            documents: list[DocumentModel] = await self.repository.get_by_type(user.id, [1, 2, 3])

            if not documents:
                raise ValueError('Documento não encontrado')

            return [DocumentMapper.model_to_schema(document) for document in documents]
        except Exception as e:
            await ApplicationLogger.log_error(e, reraise=True)

    async def get_management_document_template(
        self,
        document_type_id: int,
        component_id: Optional[UUID],
        month: Optional[int]
    ) -> Optional[dict[str, str]]:
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
                        raise ValueError('ID do componente inválido')
                    if not month or month <= 0 or month > 12:
                        raise ValueError('Mês inválido')
                    document_base64 = await self._get_attendance_list_template(component_id, month)
                case _:
                    return None

            random_code: str = str(uuid4()).replace('-', '')
            fileName: str = f'arquivo_{random_code}.pdf'

            if not document_base64.startswith('data'):
                document_base64 = f'data:application/pdf;base64,{document_base64}'

            return {
                'fileName': fileName,
                'base64': document_base64
            }
        except Exception as e:
            await ApplicationLogger.log_error(e, reraise=True)
    
    async def delete_document(self, document_id: UUID) -> bool:
        """Delete a document"""
        try:
            document: DocumentModel | None = await self.repository.get_by_id(document_id)

            if not document:
                raise ValueError("Nenhum documento encontrado")
            
            deleted: bool = await self.repository.delete(document_id)
            await self.repository.session.commit()

            return deleted
        except Exception as e:
            await ApplicationLogger.log_error(e, reraise=True)

    async def get_user_subscription_form(self, user_id: UUID) -> str:
        """Returns base64-encoded PDF of the registration form for an existing user"""
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise ValueError("Usuário não encontrado")

        addresses = await self.address_repo.get_by_user_id(user_id)
        address = addresses[0] if addresses else None

        representatives = await self.representative_repo.get_by_user_id(user_id)
        rep1 = representatives[0] if len(representatives) > 0 else None
        rep2 = representatives[1] if len(representatives) > 1 else None

        sex = await self.sex_type_repo.get_by_id_int(user.sex_id)
        gender = await self.gender_type_repo.get_by_id_int(user.gender_id)

        values = {
            "email": user.email or "",
            "userDocumentType": "CPF",
            "userDocument": self._format_document(user.document),
            "userName": user.name,
            "birthdate": user.birthdate.strftime("%d/%m/%Y"),
            "cellphone": self._format_phone(user.cellphone_number),
            "cellphone2": self._format_phone(user.contact_cellphone_number),
            "sexOptions": self._render_checkbox_group(
                ["Feminino", "Masculino"],
                sex.description if sex else None,
            ),
            "genderOptions": self._render_checkbox_group(
                ["Mulher", "Homem", "Não-binário", "Outro", "Prefiro não informar"],
                gender.description if gender else None,
            ),
            "school": user.school or "",
            "zipCode": self._format_zip(address.zip_code) if address else "",
            "street": address.street if address else "",
            "addressNumber": address.number if address else "",
            "addressComplement": (address.complement or "") if address else "",
            "neighborhood": address.neighborhood if address else "",
            **await self._representative_values(1, rep1),
            **await self._representative_values(2, rep2),
        }

        with open("src/templates/docs/user_subscription_form_template.html", "r", encoding="utf-8") as f:
            html = f.read()

        html = self._replace_placeholders(html, values)
        html = self._strip_placeholders(html)
        base64 = PdfRenderService.render_to_base64(html)

        if not base64.startswith('data'):
            base64 = f"data:application/pdf;base64,{base64}"

        return base64

    # Private methods
    async def _representative_values(self, n: int, rep) -> dict:
        if not rep:
            return {
                f"representative{n}Name": "",
                f"representative{n}Degree": "",
                f"representative{n}DocumentType": "",
                f"representative{n}Document": "",
            }
        degree = await self.degree_repo.get_by_id_int(rep.legal_representative_degree_id)
        return {
            f"representative{n}Name": rep.name,
            f"representative{n}Degree": degree.description if degree else "",
            f"representative{n}DocumentType": "CPF",
            f"representative{n}Document": self._format_document(rep.document),
        }

    def _replace_placeholders(self, html: str, values: dict) -> str:
        import re

        def replacer(match):
            key = match.group(1)
            return str(values[key]) if key in values else match.group(0)

        return re.sub(r"\$\{([^}]*)\}", replacer, html)

    def _strip_placeholders(self, text: str) -> str:
        return re.sub(r'\$\{[^}]*\}', '', text)

    def _render_checkbox_group(self, options: list[str], selected: str | None) -> str:
        return "".join(
            f'<label><input type="checkbox"{" checked" if o == selected else ""}>{o}</label>\n'
            for o in options
        )

    @staticmethod
    def _format_document(document: str | None) -> str:
        if not document:
            return ""
        d = "".join(filter(str.isdigit, document))
        return f"{d[:3]}.{d[3:6]}.{d[6:9]}-{d[9:]}" if len(d) == 11 else document

    @staticmethod
    def _format_phone(phone: str | None) -> str:
        if not phone:
            return ""
        d = "".join(filter(str.isdigit, phone))
        if len(d) == 11:
            return f"({d[:2]}) {d[2:7]}-{d[7:]}"
        if len(d) == 10:
            return f"({d[:2]}) {d[2:6]}-{d[6:]}"
        return phone

    @staticmethod
    def _format_zip(zip_code: str | None) -> str:
        if not zip_code:
            return ""
        d = "".join(filter(str.isdigit, zip_code))
        return f"{d[:5]}-{d[5:]}" if len(d) == 8 else zip_code

    async def _create_pending_validation(self, document: DocumentModel) -> None:
        """Create pending validation for secretary review"""
        from uuid import uuid4
        from src.domain.schemas.document_validation import DocumentValidationInput
        from src.application.mappers.document_validation_mapper import DocumentValidationMapper
        from src.data.repositories.document_validation_repository import DocumentValidationRepository
        doc_validation_repo = DocumentValidationRepository(self.repository.session)
        
        dto = DocumentValidationInput(
            id=uuid4(),
            created_at=DateTimeHandler.now(),
            updated_at=None,
            rejection_reason=None,
            document_validation_status_type_id=1,  # Pending
            document_id=document.id
        )
        model: DocumentValidationModel = DocumentValidationMapper.create_to_model(dto)
        await doc_validation_repo.create(model)

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
            card_html = card_html.replace('${studentPhotoBase64}', photo_base_64)
            user_address = (await self.address_repo.get_by_user_id(user.id))[0]
            card_html = card_html.replace(
                '${userFullAddress}',
                f'{user_address.street}, {user_address.number} - {user_address.neighborhood}, {FormatHandler.format_zip_code(user_address.zip_code)}' if user_address else ''
            )
            student_phone_number = user.cellphone_number if user.cellphone_number else ''
            card_html = card_html.replace('${userPhoneNumber}', FormatHandler.format_phone(student_phone_number))

        # print(card_html[:578492])
        pdfBase64 = self._render_to_base64(card_html)
        
        if not pdfBase64.startswith('data:'):
            pdfBase64 = f'data:application/pdf;base64,{pdfBase64}'

        return pdfBase64
    
    async def _create_student_card(self, user: UserModel, photo_base_64: str) -> DocumentCreate:
        user_id: UUID = user.id
        dto: DocumentCreate = DocumentCreate(
            base64=self._get_student_card_base64(user, photo_base_64),
            user_id=str(user_id),
            document_type_id=8,
            is_front=None,
            legal_representative_id=None
        )
        model: DocumentModel = DocumentMapper.create_to_model(dto)
        model.user_id = user.id

        await self.repository.create(model)
    
    # Health certificate
    def _get_health_certificate_template(self) -> str:
        """Get the health certificate template"""
        with open('src/templates/docs/health_certificate.html', 'r', encoding='utf-8') as f:
            return self._render_to_base64(f.read())

    # Register user form template
    def _get_register_user_form_template(self) -> str:
        "Get the register user form template"
        html = ''
        with open('src/templates/docs/register_user_form_template.html', 'r', encoding='utf-8') as f:
            html = f.read()
        
        html = self._strip_placeholders(html)
        
        return self._render_to_base64(html)
    
    # Attendance list template
    def _generate_attendance_list_day_wrappers(self, classes_in_month: list[ClassModel]) -> str:
        WEEKDAYS: List[str] = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]
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
        enrollments: list[EnrollmentModel],
        classes_count: int
    ) -> str:
        ATTENDANCE_CELL: str = '<td class="attendance_check"></td>'
        RESULT_CELL: str = '<td class="attended_count"></td><td class="absence_count"></td>'
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
        attendance_cells: str = ATTENDANCE_CELL * classes_count
        
        count: int = 1
        for enrollment in enrollments:
            user: UserModel | None = await self.user_repo.get_by_id(enrollment.user_id)

            if not user:
                continue
            
            row: str = STUDENT_ROW_HTML.replace('${studentPosition}', str(count))
            row = row.replace('${studentName}', user.name)
            row = row.replace('${attendanceCells}', attendance_cells)
            row = row.replace('${resultCells}', RESULT_CELL)
            result_html += row
            count += 1
        
        return result_html
    
    def _get_schedule_description(self, classes_in_month: List[ClassModel]) -> str:
        """Returns: 'Segunda, Terça, Quarta\n10h00'"""
        WEEKDAYS_FULL: List[str] = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]
        seen: set = set()
        time: str = classes_in_month[0].date.strftime("%Hh%M") if classes_in_month else ""
        
        for class_ in classes_in_month:
            seen.add(class_.date.weekday())
        
        sorted_days: List[date] = sorted(seen)
        day_names: List[str] = [WEEKDAYS_FULL[d] for d in sorted_days]
        
        return f"{', '.join(day_names)}<br>{time}"

    async def _get_attendance_list_template(self, component_id: UUID, month: int) -> str:
        """Get the attendance list template"""
        if month <= 0 or month > 12:
            raise ValueError('Mês inválido')

        from src.data.models.course_model import CourseModel
        from src.data.models.course_component_model import CourseComponentModel
        from src.data.repositories.enrollment_repository import EnrollmentRepository
        from src.data.repositories.course_repository import CourseRepository
        from src.data.repositories.course_component_repository import CourseComponentRepository
        from src.data.repositories.class_repository import ClassRepository

        enrollment_repo = EnrollmentRepository(self.repository.session)
        course_repo = CourseRepository(self.repository.session)
        component_repo = CourseComponentRepository(self.repository.session)
        class_repo = ClassRepository(self.repository.session)

        component: CourseComponentModel = await component_repo.get_by_id(component_id)

        if not component:
            raise ValueError('Componente não existe')
        
        classes_in_month: List[ClassModel] = await class_repo.get_by_component_and_month(component_id, month)
        class_count: int = len(classes_in_month)

        if class_count == 0:
            raise ValueError('Nenhuma aula encontrada para o mês')
        
        course: CourseModel = await course_repo.get_by_id(component.course_id)

        if not course:
            raise ValueError('Curso não encontrado')
        
        enrollments: List[EnrollmentModel] = await enrollment_repo.get_active_by_course_id(course.id)

        if len(enrollments) == 0:
            raise ValueError('Nenhuma matricula encontrada para o curso')
        
        educator: UserModel = await self.user_repo.get_by_id(course.responsible_educator_1)

        if not educator:
            raise ValueError('Educador responsável não encontrado')

        html: str = ''
        with open('src/templates/docs/attendance_list_template.html', 'r', encoding='utf-8') as f:
            html = f.read()

        if len(html) > 0:
            html = html.replace('${responsibleName}', educator.name)
            html = html.replace('${responsibleOccupation}', '')
            html = html.replace('${classCodeOnEol}', '')
            html = html.replace('${componentName}', component.name)
            html = html.replace('${ageGroup}', '')
            html = html.replace('${classTimeDays}', self._get_schedule_description(classes_in_month))
            html = html.replace('${class}', '')
            html = html.replace('${day_wrappers}', self._generate_attendance_list_day_wrappers(classes_in_month))
            html = html.replace('${studentRows}', await self._generate_attendance_list_student_rows(enrollments, class_count))
            
            return self._render_to_base64(html)

        return '';
