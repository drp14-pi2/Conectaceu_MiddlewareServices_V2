from uuid import UUID

from src.application.logging.application_logger import ApplicationLogger
from src.data.models.class_model import ClassModel
from src.data.models.course_component_model import CourseComponentModel
from src.data.models.course_model import CourseModel
from src.data.models.document_model import DocumentModel
from src.data.models.enrollment_model import EnrollmentModel
from src.data.models.legal_representative_model import LegalRepresentativeModel
from src.data.models.user_model import UserModel
from src.data.repositories.class_repository import ClassRepository
from src.data.repositories.course_component_repository import CourseComponentRepository
from src.data.repositories.course_repository import CourseRepository
from src.data.repositories.user_repository import UserRepository
from src.data.repositories.document_repository import DocumentRepository
from src.data.repositories.enrollment_repository import EnrollmentRepository
from src.data.repositories.legal_representative_repository import LegalRepresentativeRepository
from src.domain.schemas.class_attendance import AttendanceEntry


class SecurityService():
    def __init__(
        self,
        class_repo: ClassRepository,
        component_repo: CourseComponentRepository,
        course_repo: CourseRepository,
        user_repo: UserRepository,
        document_repo: DocumentRepository,
        enrollment_repo: EnrollmentRepository,
        representative_repo: LegalRepresentativeRepository
    ):
        self.class_repo = class_repo
        self.component_repo = component_repo
        self.course_repo = course_repo
        self.user_repo = user_repo
        self.document_repo = document_repo
        self.enrollment_repo = enrollment_repo
        self.representative_repo = representative_repo
    
    async def can_access_educational_unit(self, user_id: UUID, educational_unit_id: UUID) -> bool:
        try:
            user: UserModel | None = await self.user_repo.get_by_id(user_id)

            if not user:
                raise ValueError('Usuário não encontrado')

            # Master administrator can access any unit
            # Other users can only access their own
            return user.user_type_id == 1 or user.educational_unit_id == educational_unit_id
        except Exception as e:
            await ApplicationLogger.log_error(e)

            return False;
    
    async def can_access_other_user(self, accessor_id: UUID, accessed_id: UUID) -> bool:
        try:
            accessor_user: UserModel | None = await self.user_repo.get_by_id(accessor_id)

            if not accessor_user:
                raise ValueError('Acessor não encontrado')
            elif accessor_user.user_type_id == 1:
                return True

            accessed_user: UserModel | None = await self.user_repo.get_by_id(accessed_id)

            if not accessed_user:
                raise ValueError('Usuário a acessar não encontrado')

            # Master administrator can access any unit
            # Other users can only access in their own educational unit
            return accessor_user.educational_unit_id == accessed_user.educational_unit_id
        except Exception as e:
            await ApplicationLogger.log_error(e)

            return False;
    
    async def can_access_other_users(self, accessor_id: UUID, accessed_ids: list[UUID]) -> bool:
        try:
            accessor_user: UserModel | None = await self.user_repo.get_by_id(accessor_id)

            if not accessor_user:
                raise ValueError('Acessor não encontrado')
            elif accessor_user.user_type_id == 1:
                return True

            for accessed_id in accessed_ids:
                if not await self.can_access_other_user(accessor_id, accessed_id):
                    return False

            return True
        except Exception as e:
            await ApplicationLogger.log_error(e)

            return False;

    async def can_access_course(self, user_id: UUID, course_id: UUID) -> bool:
        try:
            user: UserModel | None = await self.user_repo.get_by_id(user_id)

            if not user:
                raise ValueError('Usuário não encontrado')
            elif user.user_type_id == 1:
                return True

            course: CourseModel | None = await self.course_repo.get_by_id(course_id)

            if not course:
                raise ValueError('Curso não encontrado')

            return user.educational_unit_id == course.educational_unit_id
        except Exception as e:
            await ApplicationLogger.log_error(e)

            return False

    async def can_access_component(self, user_id: UUID, component_id: UUID) -> bool:
        try:
            user: UserModel | None = await self.user_repo.get_by_id(user_id)

            if not user:
                raise ValueError('Usuário não encontrado')
            elif user.user_type_id == 1:
                return True

            component: CourseComponentModel | None = await self.component_repo.get_by_id(component_id)

            if not component:
                raise ValueError('Componente não encontrado')

            course: CourseModel | None = await self.course_repo.get_by_id(component.course_id)

            if not course:
                raise ValueError('Curso não encontrado')

            return user.educational_unit_id == course.educational_unit_id
        except Exception as e:
            await ApplicationLogger.log_error(e)

            return False

    async def are_users_in_educational_unit(self, educational_unit_id: UUID, users_ids: list[UUID]) -> bool:
        try:
            for user_id in users_ids:
                user: UserModel | None = await self.user_repo.get_by_id(user_id)

                if user and user.educational_unit_id == educational_unit_id:
                    return True

            return False
        except Exception as e:
            await ApplicationLogger.log_error(e)

            return True

    async def can_access_class(self, user_id: UUID, class_id: UUID) -> bool:
        try:
            user: UserModel | None = await self.user_repo.get_by_id(user_id)

            if not user:
                raise ValueError('Usuário não encontrado')
            elif user.user_type_id == 1:
                return True

            class_: ClassModel | None = await self.class_repo.get_by_id(class_id)

            if not class_:
                raise ValueError('Aula não encontrada')

            component: CourseComponentModel | None = await self.component_repo.get_by_id(class_.course_component_id)

            if not component:
                raise ValueError('Componente não encontrado')

            course: CourseModel | None = await self.course_repo.get_by_id(component.course_id)

            if not course:
                raise ValueError('Curso não encontrado')

            return user.educational_unit_id == course.educational_unit_id
        except Exception as e:
            await ApplicationLogger.log_error(e)

            return False

    async def can_user_create_attendance(self, creator_id: UUID, course_id: UUID, attendance_entries: list[AttendanceEntry]) -> bool:
        try:
            attendees_ids: list[UUID] = [entry.user_id for entry in attendance_entries]
            
            return self.can_access_course(creator_id, course_id) and self.are_users_in_educational_unit(creator_id, attendees_ids)
        except Exception as e:
            await ApplicationLogger.log_error(e)

            return False

    async def can_access_document(self, creator_id: UUID, document_id: UUID) -> bool:
        try:
            creator_user: UserModel | None = await self.user_repo.get_by_id(creator_id)

            if not creator_user:
                raise ValueError('Usuário criador não encontrado')
            elif creator_user.user_type_id == 1:
                return True
            
            document: DocumentModel | None = await self.document_repo.get_by_id(document_id)

            if not document:
                raise ValueError('Documento não encontrado')

            document_owner: UserModel | None = await self.user_repo.get_by_id(document.user_id)

            if not document_owner:
                raise ValueError('Usuário proprietário do documento não encontrado')

            return creator_user.educational_unit_id == document_owner.educational_unit_id
        except Exception as e:
            await ApplicationLogger.log_error(e)

            return False

    async def can_enroll_users(self, creator_id: UUID, students_ids: list[UUID], course_id: UUID) -> bool:
        try:
            return self.can_access_other_users(creator_id, students_ids) and self.can_access_course(creator_id, course_id)
        except Exception as e:
            await ApplicationLogger.log_error(e)

            return False

    async def can_access_enrollment(self, user_id: UUID, enrollment_id) -> bool:
        try:
            user: UserModel | None = await self.user_repo.get_by_id(user_id)

            if not user:
                raise ValueError('Usuário não encontrado')
            elif user.user_type_id == 1:
                return True

            enrollment: EnrollmentModel | None = await self.enrollment_repo.get_by_id(enrollment_id)

            if not enrollment:
                raise ValueError('Matrícula não encontrada')

            course: CourseModel | None = await self.course_repo.get_by_id(enrollment.course_id)

            if not course:
                raise ValueError('Curso não encontrado')

            return user.educational_unit_id == course.educational_unit_id
        except Exception as e:
            await ApplicationLogger.log_error(e)

            return False

    async def can_access_representative(self, user_id: UUID, representative_id: UUID) -> bool:
        try:
            user: UserModel | None = await self.user_repo.get_by_id(user_id)

            if not user:
                raise ValueError('Usuário não encontrado')
            elif user.user_type_id == 1:
                return True

            representative: LegalRepresentativeModel | None = await self.representative_repo.get_by_id(representative_id)

            if not representative:
                raise ValueError('Representante legal não encontrado')

            represented_user: UserModel | None = await self.user_repo.get_by_id(representative.user_id)

            if not represented_user:
                raise ValueError('Usuário não encontrado')

            return user.educational_unit_id == represented_user.educational_unit_id
        except Exception as e:
            await ApplicationLogger.log_error(e)

            return False
