"""User mapper - converts between UserModel and User schema"""
from src.data.models.user_model import UserModel
from src.domain.schemas.user import User, UserCreate, UserUpdate

class UserMapper:
    @staticmethod
    def model_to_schema(model: UserModel) -> User:
        return User.model_validate(model)

    @staticmethod
    def create_to_model(dto: UserCreate) -> UserModel:
        return UserModel(
            document=dto.document,
            name=dto.name,
            email=dto.email,
            cellphone_number=dto.cellphone_number,
            contact_cellphone_number=dto.contact_cellphone_number,
            password=dto.password,
            birthdate=dto.birthdate,
            school=dto.school,
            sex_id=dto.sex_id,
            gender_id=dto.gender_id,
            user_type_id=dto.user_type_id
        )

    @staticmethod
    def update_model(model: UserModel, dto: UserUpdate) -> UserModel:
        for field, value in dto.model_dump(exclude_none=True).items():
            setattr(model, field, value)
        return model
