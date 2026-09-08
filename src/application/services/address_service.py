"""Address service - business logic for Address entity"""
from typing import List, Optional
from uuid import UUID

from src.application.logging.application_logger import ApplicationLogger
from src.data.models.address_model import AddressModel
from src.data.repositories.address_repository import AddressRepository
from src.application.services.base_service import BaseService
from src.domain.schemas.address import Address, AddressCreate, AddressUpdate
from src.application.mappers.address_mapper import AddressMapper

class AddressService(BaseService):
    """Service for Address business logic"""
    
    def __init__(self, repository: AddressRepository):
        super().__init__(repository, 'address', mapper_class=AddressMapper)
        self.repository = repository
    
    async def create_address(self, dto: AddressCreate) -> Address:
        """Create a new address"""
        try:
            model: AddressModel | None = AddressMapper.create_to_model(dto)
            saved_model: AddressModel = await self.repository.create(model)
            self.repository.session.commit()

            return AddressMapper.model_to_schema(saved_model)
        except Exception as e:
            await ApplicationLogger.log_error(e, reraise=True)
    
    async def update_address(self, address_id: UUID, dto: AddressUpdate) -> Address:
        """Update an address"""
        try:
            model: AddressModel | None = await self.repository.get_by_id(address_id)

            if not model:
                raise ValueError("Endereço não encontrado")
            
            updated_model: AddressModel = AddressMapper.update_model(model, dto)
            saved_model: AddressModel = await self.repository.update(updated_model)
            self.repository.session.commit()

            return AddressMapper.model_to_schema(saved_model)
        except Exception as e:
            await ApplicationLogger.log_error(e, reraise=True)
    
    async def get_user_addresses(self, user_id: UUID) -> List[Address]:
        """Get all addresses for a user"""
        try:
            models: List[AddressModel] = await self.repository.get_by_user_id(user_id)

            return [AddressMapper.model_to_schema(model) for model in models]
        except Exception as e:
            await ApplicationLogger.log_error(e, reraise=True)
    
    async def get_primary_address(self, user_id: UUID) -> Optional[Address]:
        """Get user's primary address"""
        try:
            model: AddressModel | None = await self.repository.get_primary_address(user_id)

            if not model:
                raise ValueError("Endereço não encontrado")

            return AddressMapper.model_to_schema(model)
        except Exception as e:
            await ApplicationLogger.log_error(e, reraise=True)
