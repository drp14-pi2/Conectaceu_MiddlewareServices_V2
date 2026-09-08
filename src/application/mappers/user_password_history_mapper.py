from src.data.models.user_password_history_model import UserPasswordHistoryModel
from src.domain.schemas.user_password_history import UserPasswordHistory, UserPasswordHistoryCreate

class UserPasswordHistoryMapper:
    @staticmethod
    def model_to_schema(model: UserPasswordHistoryModel) -> UserPasswordHistory:
        return UserPasswordHistory.model_validate(model)

    @staticmethod
    def create_to_model(dto: UserPasswordHistoryCreate) -> UserPasswordHistoryModel:
        return UserPasswordHistoryModel(**dto.model_dump())
