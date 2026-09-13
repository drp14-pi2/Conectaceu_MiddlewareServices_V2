"""Base repository with common CRUD operations"""
from typing import TypeVar, Generic, Optional, List, Type
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from src.data.db_context.base import Base

T = TypeVar('T', bound=Base) # pyright: ignore[reportInvalidTypeForm]

class BaseRepository(Generic[T]):
    """Generic repository with common operations"""
    
    def __init__(self, session: Session, model_class: Type[T]):
        self.session = session
        self.model_class = model_class
    
    async def create(self, entity: T) -> T:
        """Create a new entity"""
        self.session.add(entity)
        self.session.flush()
        return entity
    
    async def get_by_id(self, id: UUID) -> Optional[T]:
        """Get entity by UUID"""
        stmt = select(self.model_class).where(self.model_class.id == id)
        result = self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_by_id_int(self, id: int) -> Optional[T]:
        """Get entity by integer ID (for reference tables)"""
        stmt = select(self.model_class).where(self.model_class.id == id)
        result = self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        """Get all entities with pagination"""
        stmt = select(self.model_class).offset(skip).limit(limit)
        result = self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def update(self, entity: T) -> T:
        """Update an entity"""
        self.session.merge(entity)
        self.session.flush()
        return entity
    
    async def delete(self, id: UUID) -> bool:
        """Hard delete an entity"""
        model = await self.get_by_id(id)
        if model:
            self.session.delete(model)
            self.session.flush()
            return True
        return False
    
    async def delete_int(self, id: int) -> bool:
        """Hard delete an entity with integer ID"""
        entity = self.get_by_id_int(id)
        if entity:
            self.session.delete(entity)
            self.session.flush()
            return True
        return False
    
    async def count(self, filters: dict = None) -> int:
        """Count entities with optional filters"""
        stmt = select(func.count()).select_from(self.model_class)
        if filters:
            for key, value in filters.items():
                if hasattr(self.model_class, key) and value is not None:
                    stmt = stmt.where(getattr(self.model_class, key) == value)
        result = self.session.execute(stmt)
        return result.scalar()
    
    async def exists(self, id: UUID) -> bool:
        """Check if entity exists"""
        entity = self.get_by_id(id)
        return entity is not None
    
    async def exists_int(self, id: int) -> bool:
        """Check if entity with integer ID exists"""
        entity = self.get_by_id_int(id)
        return entity is not None
