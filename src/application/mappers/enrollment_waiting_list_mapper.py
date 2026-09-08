"""Enrollment waiting list mapper"""
from src.data.models.enrollment_waiting_list_model import EnrollmentWaitingListModel
from src.domain.schemas.enrollment_waiting_list import EnrollmentWaitingList

class EnrollmentWaitingListMapper:
    @staticmethod
    def model_to_schema(model: EnrollmentWaitingListModel) -> EnrollmentWaitingList:
        return EnrollmentWaitingList.model_validate(model)
