from sqlalchemy import Column, DateTime, ForeignKey, String, func

from src.data.db_context.base import Base
from src.data.db_context.types import UUIDBinary

class EmailValidationModel(Base):
    __tablename__ = 'email_validation'

    user_id = Column(UUIDBinary, ForeignKey('user.id'), primary_key=True)
    token = Column(String(64), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
