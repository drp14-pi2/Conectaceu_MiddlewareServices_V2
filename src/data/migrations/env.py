"""Alembic environment configuration"""
import sys
from pathlib import Path
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.data.db_context.base import Base
from src.infrastructure.configuration.settings import settings

# Import all models so Alembic can detect them
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
from src.data.models.enrollment_waiting_list_model import EnrollmentWaitingListModel

# Log models
from src.data.models.log_application_error_model import LogApplicationErrorModel
from src.data.models.log_broadcast_message_model import LogBroadcastMessageModel
from src.data.models.log_course_creation_model import LogCourseCreationModel
from src.data.models.log_document_request_model import LogDocumentRequestModel
from src.data.models.log_document_validation_model import LogDocumentValidationModel
from src.data.models.log_report_request_model import LogReportRequestModel
from src.data.models.log_student_enrollment_model import LogStudentEnrollmentModel
from src.data.models.log_user_activation_model import LogUserActivationModel

# This is the Alembic Config object
config = context.config

# Override sqlalchemy.url with our config
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Add your model's MetaData object for 'autogenerate' support
target_metadata = Base.metadata

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()