"""Base repository with common CRUD operations"""
from typing import TypeVar, Generic, Optional, List, Type
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from src.data.db_context.base import Base

T = TypeVar('T', bound=Base) # pyright: ignore[reportInvalidTypeForm]

class BaseRepository(Generic[T]):
    """Generic repository with common operations"""
    
    def __init__(self, session: AsyncSession, model_class: Type[T]):
        self.session = session
        self.model_class = model_class
    
    async def create(self, entity: T) -> T:
        """Create a new entity"""
        self.session.add(entity)
        await self.session.flush()
        return entity
    
    async def get_by_id(self, id: UUID) -> Optional[T]:
        """Get entity by UUID"""
        stmt = select(self.model_class).where(self.model_class.id == id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_by_id_int(self, id: int) -> Optional[T]:
        """Get entity by integer ID (for reference tables)"""
        stmt = select(self.model_class).where(self.model_class.id == id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        """Get all entities with pagination"""
        stmt = select(self.model_class).offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def update(self, entity: T) -> T:
        """Update an entity"""
        await self.session.merge(entity)
        await self.session.flush()
        return entity
    
    async def delete(self, id: UUID) -> bool:
        """Hard delete an entity"""
        model = await self.get_by_id(id)
        if model:
            await self.session.delete(model)
            await self.session.flush()
            return True
        return False
    
    async def delete_int(self, id: int) -> bool:
        """Hard delete an entity with integer ID"""
        entity = await self.get_by_id_int(id)
        if entity:
            await self.session.delete(entity)
            await self.session.flush()
            return True
        return False
    
    async def count(self, filters: dict = None) -> int:
        """Count entities with optional filters"""
        stmt = select(func.count()).select_from(self.model_class)
        if filters:
            for key, value in filters.items():
                if hasattr(self.model_class, key) and value is not None:
                    stmt = stmt.where(getattr(self.model_class, key) == value)
        result = await self.session.execute(stmt)
        return result.scalar()
    
    async def exists(self, id: UUID) -> bool:
        """Check if entity exists"""
        entity = await self.get_by_id(id)
        return entity is not None
    
    async def exists_int(self, id: int) -> bool:
        """Check if entity with integer ID exists"""
        entity = await self.get_by_id_int(id)
        return entity is not None
