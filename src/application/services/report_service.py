"""Report service - generate reports from data"""
import decimal
from typing import List, Dict, Any, Optional
from uuid import UUID

from src.application.logging.application_logger import ApplicationLogger
from src.data.models.class_model import ClassModel
from src.data.models.course_component_model import CourseComponentModel
from src.data.models.course_model import CourseModel
from src.data.models.enrollment_model import EnrollmentModel
from src.data.models.user_model import UserModel
from src.data.repositories.class_repository import ClassRepository
from src.data.repositories.course_component_repository import CourseComponentRepository
from src.data.repositories.log_report_request_repository import LogReportRequestRepository
from src.data.repositories.course_repository import CourseRepository
from src.data.repositories.enrollment_repository import EnrollmentRepository
from src.data.repositories.user_repository import UserRepository
from src.infrastructure.pdf.pdf_render_service import PdfRenderService

WEEKDAYS = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]

class ReportService:
    """Service for generating reports"""
    
    def __init__(
        self,
        course_repo: CourseRepository,
        component_repo: CourseComponentRepository,
        enrollment_repo: EnrollmentRepository,
        user_repo: UserRepository,
        class_repo: ClassRepository,
        log_report_repo: LogReportRequestRepository
    ):
        self.course_repo = course_repo
        self.component_repo = component_repo
        self.enrollment_repo = enrollment_repo
        self.user_repo = user_repo
        self.class_repo = class_repo
        self.log_report_repo = log_report_repo
    
    async def get_students_by_course(
        self,
        course_id: Optional[UUID] = None,
        educational_unit_id: Optional[UUID] = None,
        requested_by_user_id: Optional[UUID] = None,
        user_ip_address: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get students enrolled by course and/or component.
        """
        try:
            if requested_by_user_id:
                await self.log_report_repo.log(
                    report_type_id=1,
                    user_id=requested_by_user_id,
                    user_ip_address=user_ip_address or "unknown"
                )

            courses: List[CourseModel] = []
            report_data: List[dict[str, Any]] = []
            
            if course_id:
                course: CourseModel | None = await self.course_repo.get_by_id(course_id)

                if course:
                    if educational_unit_id and course.educational_unit_id != educational_unit_id:
                        return report_data;

                    courses.append(course)
            else:
                if educational_unit_id:
                    courses = await self.course_repo.find_by_filters(educational_unit_id=educational_unit_id)
                else:
                    courses = await self.course_repo.get_all()
            
            for course in courses:
                course_uuid: UUID = course.id
                enrollments: List[EnrollmentModel] = await self.enrollment_repo.get_active_by_course_id(course_uuid)
                
                for enrollment in enrollments:
                    user_uuid: UUID = enrollment.user_id
                    user: UserModel | None = await self.user_repo.get_by_id(user_uuid)
                    
                    if not user:
                        continue
                    
                    report_data.append({
                        'course_id': str(course_uuid),
                        'course_name': course.name,
                        'shift_type_id': course.shift_type_id,
                        'student_name': user.name,
                        'student_document': user.document,
                        'student_email': user.email,
                        'student_phone': user.cellphone_number
                    })

            return report_data
        except Exception as e:
            await ApplicationLogger.log_error(e, reraise=True)
    
    async def get_course_vacancies(
        self,
        course_id: Optional[UUID] = None,
        educational_unit_id: Optional[UUID] = None,
        requested_by_user_id: Optional[UUID] = None,
        user_ip_address: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get vacancies by course"""
        try:
            if requested_by_user_id:
                await self.log_report_repo.log(
                    report_type_id=2,
                    user_id=requested_by_user_id,
                    user_ip_address=user_ip_address or "unknown"
                )
                
            report_data: List[dict[str, Any]] = []
            courses: List[CourseModel] = []
            
            if course_id:
                course: CourseModel | None = await self.course_repo.get_by_id(course_id)

                if course:
                    if educational_unit_id and course.educational_unit_id != educational_unit_id:
                        return report_data;

                    courses.append(course)
            else:
                if educational_unit_id:
                    courses = await self.course_repo.find_by_filters(educational_unit_id=educational_unit_id)
                else:
                    courses = await self.course_repo.get_all()
            
            for course in courses:
                course_uuid: UUID = course.id
                # Count enrollments directly by course
                enrollments: List[EnrollmentModel] = await self.enrollment_repo.get_active_by_course_id(course_uuid)
                total_enrolled: int = len(enrollments)
                report_data.append({
                    'course_id': str(course_uuid),
                    'course_name': course.name,
                    'total_seats': course.total_seat_limit,
                    'enrolled': total_enrolled,
                    'available_seats': course.total_seat_limit - total_enrolled,
                    'occupation_rate': self._get_occupation_rate(total_enrolled, course.total_seat_limit)
                })

            return report_data
        except Exception as e:
            await ApplicationLogger.log_error(e, reraise=True)

    async def render_user_courses_pdf(self, user_id: UUID) -> str:
        try:
            user = await self.user_repo.get_by_id(user_id)
            if not user:
                raise ValueError("Usuário não encontrado")

            enrollments = await self.enrollment_repo.get_active_by_user_id(user_id)

            rows_html = ""
            for enrollment in enrollments:
                course = await self.course_repo.get_by_id(enrollment.course_id)
                if not course:
                    continue

                components = await self.component_repo.get_by_course_id(course.id)

                for component in components:
                    classes = await self.class_repo.get_by_component_id(component.id)
                    period = self._format_component_range(classes)

                    rows_html += (
                        "<tr>"
                        f"<td>{course.name}</td>"
                        f"<td>{component.name}</td>"
                        f"<td>{period}</td>"
                        "</tr>"
                    )

            with open("src/templates/docs/user_courses_report.html", "r", encoding="utf-8") as f:
                html = f.read()

            html = html.replace("${userName}", user.name)
            html = html.replace(
                "${rows}",
                rows_html or '<tr><td colspan="3">Nenhum curso encontrado</td></tr>',
            )

            base64 = PdfRenderService.render_to_base64(html)

            if not base64.startswith('data'):
                base64 = f'data:application/pdf;base64,{base64}'

            return base64
        except Exception as e:
            await ApplicationLogger.log_error(e, reraise=True)

    # Private methods
    def _format_component_range(self, classes: List[ClassModel]) -> str:
        """Format a component's classes as first–last dates + weekdays"""
        if not classes:
            return "Sem aulas cadastradas"

        dates = sorted(c.date for c in classes)
        first, last = dates[0], dates[-1]

        weekdays = sorted({WEEKDAYS[d.weekday()] for d in dates})
        days_text = ", ".join(weekdays)

        if first.date() == last.date():
            return f"{first.strftime('%d/%m/%Y')} ({days_text})"

        return f"{first.strftime('%d/%m/%Y')} a {last.strftime('%d/%m/%Y')} ({days_text})"

    def _format_class(self, class_model) -> str:
        start = class_model.date.strftime("%d/%m/%Y")
        weekday = WEEKDAYS[class_model.date.weekday()]
        end = getattr(class_model, "end_date", None)
        end_str = end.strftime("%d/%m/%Y") if end else "—"
        return f"{start} a {end_str} ({weekday})"

    def _format_classes(self, classes: List) -> str:
        return ", ".join(self._format_class(c) for c in classes)

    def _get_occupation_rate(self, total_enrolled: int, total_seat_limit: int) -> decimal:
        occupation_rate: int = 0

        if total_enrolled > 0 and total_seat_limit > 0:
            occupation_rate = total_enrolled / total_seat_limit * 100

        return round(occupation_rate, 2)
