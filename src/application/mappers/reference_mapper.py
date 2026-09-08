"""Reference tables mapper - handles all simple reference entities"""
from src.data.models.user_sex_type_model import UserSexTypeModel
from src.data.models.user_gender_type_model import UserGenderTypeModel
from src.data.models.user_type_model import UserTypeModel
from src.data.models.document_type_model import DocumentTypeModel
from src.data.models.document_validation_status_type_model import DocumentValidationStatusTypeModel
from src.data.models.shift_type_model import ShiftTypeModel
from src.data.models.report_type_model import ReportTypeModel
from src.data.models.legal_representative_degree_model import LegalRepresentativeDegreeModel

from src.domain.schemas.reference_schemas import (
    UserSexType,
    UserGenderType,
    UserType,
    DocumentType,
    DocumentValidationStatusType,
    ShiftType,
    ReportType,
    LegalRepresentativeDegree
)

class ReferenceMapper:
    @staticmethod
    def user_sex_type_model_to_schema(model: UserSexTypeModel) -> UserSexType:
        return UserSexType.model_validate(model)

    @staticmethod
    def user_gender_type_model_to_schema(model: UserGenderTypeModel) -> UserGenderType:
        return UserGenderType.model_validate(model)

    @staticmethod
    def user_type_model_to_schema(model: UserTypeModel) -> UserType:
        return UserType.model_validate(model)

    @staticmethod
    def document_type_model_to_schema(model: DocumentTypeModel) -> DocumentType:
        return DocumentType.model_validate(model)

    @staticmethod
    def document_validation_status_type_model_to_schema(
        model: DocumentValidationStatusTypeModel,
    ) -> DocumentValidationStatusType:
        return DocumentValidationStatusType.model_validate(model)

    @staticmethod
    def shift_type_model_to_schema(model: ShiftTypeModel) -> ShiftType:
        return ShiftType.model_validate(model)

    @staticmethod
    def report_type_model_to_schema(model: ReportTypeModel) -> ReportType:
        return ReportType.model_validate(model)

    @staticmethod
    def legal_representative_degree_model_to_schema(
        model: LegalRepresentativeDegreeModel,
    ) -> LegalRepresentativeDegree:
        return LegalRepresentativeDegree.model_validate(model)

