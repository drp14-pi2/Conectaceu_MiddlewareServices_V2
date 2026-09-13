"""Report type model"""
from sqlalchemy import Column, String
from src.data.db_context.base import IntPkBaseModel

class ReportTypeModel(IntPkBaseModel):
    __tablename__ = "report_type"
    
    description = Column(String(50), unique=True, nullable=False)
