"""User mapper - converts between UserModel and User schema"""
from src.data.models.user_model import UserModel
from src.domain.schemas.user import User, UserCreate, UserUpdate

class UserMapper:
    @staticmethod
    def model_to_schema(model: UserModel) -> User:
        return User.model_validate(model)

    @staticmethod
    def create_to_model(dto: UserCreate) -> UserModel:
        return UserModel(**dto.model_dump())

    @staticmethod
    def update_model(model: UserModel, dto: UserUpdate) -> UserModel:
        for field, value in dto.model_dump(exclude_none=True).items():
            setattr(model, field, value)
        return model
