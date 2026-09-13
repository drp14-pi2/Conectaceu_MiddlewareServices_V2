from sqlalchemy import Boolean, Column, ForeignKey, String
from src.data.db_context.base import UuidPkBaseModel
from src.data.db_context.types import UUIDBinary

class LogAccessModel(UuidPkBaseModel):
    __tablename__ = 'log_access'

    success = Column(Boolean, nullable=False)
    message = Column(String(255), nullable=False)
    origin_ip_address = Column(String(39), nullable=False)
    user_agent = Column(String(255), nullable=False)

    # Foreign Keys
    user_id = Column(UUIDBinary, ForeignKey('user.id'), nullable=False)
