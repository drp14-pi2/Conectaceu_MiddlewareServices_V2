"""Base models for different entity types"""
import uuid
from sqlalchemy import Column, Integer, DateTime, func
from sqlalchemy.ext.declarative import declarative_base
from src.data.db_context.types import UUIDBinary

Base = declarative_base()

class BaseModel(Base):
    """Abstract base"""
    __abstract__ = True

class IntPkBaseModel(BaseModel):
    """Base for entities with Integer auto-increment PK"""
    __abstract__ = True
    
    id = Column(Integer, primary_key=True, autoincrement=True)

class UuidPkBaseModel(BaseModel):
    """
    Base for entities with UUID/Binary(16) PK
    - Includes creation date column
    """
    __abstract__ = True
    
    id = Column(UUIDBinary, primary_key=True, default=lambda: uuid.uuid4())
    created_at = Column(DateTime, default=func.now(), nullable=False)

class UuidPkUpdatableBaseModel(BaseModel):
    """
    Base for entities with UUID/Binary(16) PK
    - Includes audit columns
    """
    __abstract__ = True
    
    id = Column(UUIDBinary, primary_key=True, default=lambda: uuid.uuid4())
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
class LogBaseModel(BaseModel):
    """Base for log tables"""
    __abstract__ = True
    
    id = Column(UUIDBinary, primary_key=True, default=lambda: uuid.uuid4())
    created_at = Column(DateTime, default=func.now(), nullable=False)
