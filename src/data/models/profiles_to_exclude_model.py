"""Profiles to exclude model - Tracks users excluded from specific processes"""
from sqlalchemy import Boolean, Column, ForeignKey
from src.data.db_context.base import UuidPkBaseModel
from src.data.db_context.types import UUIDBinary

class ProfilesToExcludeModel(UuidPkBaseModel):
    __tablename__ = "profiles_to_exclude"

    processed = Column(Boolean, nullable=False, default=False)

    user_id = Column(UUIDBinary, ForeignKey('user.id'), nullable=False)
