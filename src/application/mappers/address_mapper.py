"""Address mapper"""
from src.data.models.address_model import AddressModel
from src.domain.schemas.address import Address, AddressCreate, AddressUpdate

class AddressMapper:
    @staticmethod
    def model_to_schema(model: AddressModel) -> Address:
        return Address.model_validate(model)

    @staticmethod
    def create_to_model(dto: AddressCreate) -> AddressModel:
        return AddressModel(**dto.model_dump())

    @staticmethod
    def update_model(model: AddressModel, dto: AddressUpdate) -> AddressModel:
        for field, value in dto.model_dump(exclude_none=True).items():
            setattr(model, field, value)
        return model
