"""User type model"""
from sqlalchemy import Column, String, Boolean
from src.data.db_context.base import IntPkBaseModel

class UserTypeModel(IntPkBaseModel):
    __tablename__ = "user_type"

    description = Column(String(50), unique=True, nullable=False)
    register_user = Column(Boolean, nullable=False, default=False)
    validate_user_documents = Column(Boolean, nullable=False, default=False)
    list_secretaries = Column(Boolean, nullable=False, default=False)
    list_educators = Column(Boolean, nullable=False, default=False)
    list_students = Column(Boolean, nullable=False, default=False)
    send_broadcast_message = Column(Boolean, nullable=False, default=False)
    add_courses = Column(Boolean, nullable=False, default=False)
    add_classes = Column(Boolean, nullable=False, default=False)
    emit_user_documents = Column(Boolean, nullable=False, default=False)
