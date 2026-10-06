"""Educational unit service - business logic for Educational unit"""
from typing import List, Optional
from uuid import UUID

from src.application.logging.application_logger import ApplicationLogger
from src.data.models.educational_unit_model import EducationalUnitModel
from src.data.repositories.educational_unit_repository import EducationalUnitRepository
from src.application.services.base_service import BaseService
from src.application.mappers.educational_unit_mapper import EducationalUnitMapper
from src.domain.schemas.educational_unit import EducationalUnit, EducationalUnitCreate, EducationalUnitUpdate

class EducationalUnitService(BaseService):
    """Service for EducationalUnit business logic"""
    
    def __init__(
        self, 
        repository: EducationalUnitRepository
    ):
        super().__init__(repository, 'educational_unit', mapper_class=EducationalUnitMapper)
        self.repository = repository

    async def create(self, dto: EducationalUnitCreate) -> EducationalUnit:
        try:
            existing: EducationalUnitModel | None = await self.repository.get_by_name_and_address(dto.name, dto.zip_code, dto.number)

            if existing:
                raise ValueError('Um polo já existe com esse nome para este endereço')

            create_model: EducationalUnitModel = EducationalUnitMapper.create_to_model(dto)
            create_model.active = True
            saved_model: EducationalUnitModel = await self.repository.create(create_model)
            await self.repository.session.commit()

            return EducationalUnitMapper.model_to_schema(saved_model)
        except Exception as e:
            await ApplicationLogger.log_error(e, reraise=True)

    async def update(self, id: UUID, dto: EducationalUnitUpdate) -> EducationalUnit:
        try:
            existing: EducationalUnitModel | None = await self.repository.get_by_id(id)

            if not existing:
                raise ValueError('Polo não encontrado')

            updated_model: EducationalUnitModel = EducationalUnitMapper.update_model(existing, dto)
            saved_model: EducationalUnitModel = await self.repository.update(updated_model)
            await self.repository.session.commit()

            return EducationalUnitMapper.model_to_schema(saved_model)
        except Exception as e:
            await ApplicationLogger.log_error(e, reraise=True)

    async def list(
        self,
        active: Optional[bool] = None
    ) -> list[EducationalUnit]:
        try:
            units: List[EducationalUnitModel] = await self.repository.list(active)

            return [EducationalUnitMapper.model_to_schema(unit) for unit in units]
        except Exception as e:
            await ApplicationLogger.log_error(e, reraise=True)
