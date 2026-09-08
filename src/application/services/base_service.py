from typing import Optional, List, Any, Type, Callable
from uuid import UUID
import re

from src.data.repositories.base.base_repository import BaseRepository

class BaseService:
    """Generic service with common CRUD operations & dynamic entity mapping"""
    
    def __init__(self, repository: BaseRepository, entity_name: str, mapper_class: Type = None):
        self.repository = repository
        self.entity_name = entity_name
        self.mapper_class = mapper_class
        self._mapper_method = self._resolve_mapper_method()
    
    def _resolve_mapper_method(self) -> Optional[Callable]:
        if not self.mapper_class:
            return None
        
        method_name = self._camel_to_snake(self.entity_name)

        return getattr(self.mapper_class, method_name, None)
    
    @staticmethod
    def _camel_to_snake(name: str) -> str:
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)

        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
    
    def _map_model(self, model: Any) -> Any:
        """Safely map a model using the resolved method, or return as-is if unavailable."""
        if self._mapper_method:
            return self._mapper_method(model)
        
        return model  # Fallback: pass-through if no specific mapper exists
    
    async def get_by_id(self, id: UUID) -> Optional[Any]:
        model = await self.repository.get_by_id(id)

        return self._map_model(model) if model else None
    
    async def get_by_id_int(self, id: int) -> Optional[Any]:
        model = await self.repository.get_by_id_int(id)

        return self._map_model(model) if model else None
    
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[Any]:
        models = await self.repository.get_all(skip, limit)

        return [self._map_model(model) for model in models]
    
    async def delete(self, id: UUID) -> bool:
        result = await self.repository.delete(id)
        self.repository.session.commit()

        return bool(result)
    
    async def delete_int(self, id: int) -> bool:
        result = await self.repository.delete_int(id)
        self.repository.session.commit()
        
        return bool(result)
    
    async def exists(self, id: UUID) -> bool:
        return await self.repository.exists(id)
    
    async def exists_int(self, id: int) -> bool:
        return await self.repository.exists_int(id)
