"""User model"""
from sqlalchemy import Column, String, DateTime, Integer, Boolean, ForeignKey
from src.data.db_context.base import UuidPkUpdatableBaseModel

class UserModel(UuidPkUpdatableBaseModel):
    __tablename__ = "user"
    
    document = Column(String(11), unique=True, nullable=False)
    name = Column(String(200), nullable=False)
    email = Column(String(120), unique=True, nullable=True)
    cellphone_number = Column(String(11), nullable=True)
    contact_cellphone_number = Column(String(11), nullable=True)
    password = Column(String(512), nullable=False)
    birthdate = Column(DateTime, nullable=False)
    school = Column(String(200), nullable=True)
    active = Column(Boolean, nullable=False, default=True)
    password_reset_token = Column(String(255), nullable=True)
    password_reset_expires = Column(DateTime, nullable=True)
    email_verified = Column(Boolean, nullable=True)
    student_sequential = Column(Integer, unique=True, nullable=True)
    
    # Foreign keys
    sex_id = Column(Integer, ForeignKey('user_sex_type.id'), nullable=False)
    gender_id = Column(Integer, ForeignKey('user_gender_type.id'), nullable=False)
    user_type_id = Column(Integer, ForeignKey('user_type.id'), nullable=False)
