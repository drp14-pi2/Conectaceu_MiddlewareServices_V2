"""Base models for different entity types"""
from datetime import datetime, timedelta, timezone
import uuid
from sqlalchemy import Column, Integer, DateTime
from sqlalchemy.ext.declarative import declarative_base
from src.data.db_context.types import UUIDBinary

Base = declarative_base()

def now():
    return datetime.now(timezone(timedelta(hours=-3)))  # Brazil GMT-3

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
    created_at = Column(DateTime, default=now, nullable=False)

class UuidPkUpdatableBaseModel(BaseModel):
    """
    Base for entities with UUID/Binary(16) PK
    - Includes audit columns
    """
    __abstract__ = True
    
    id = Column(UUIDBinary, primary_key=True, default=lambda: uuid.uuid4())
    created_at = Column(DateTime, default=now, nullable=False)
    updated_at = Column(DateTime, default=now, onupdate=now)
    
class LogBaseModel(BaseModel):
    """Base for log tables"""
    __abstract__ = True
    
    id = Column(UUIDBinary, primary_key=True, default=lambda: uuid.uuid4())
    created_at = Column(DateTime, default=now, nullable=False)
