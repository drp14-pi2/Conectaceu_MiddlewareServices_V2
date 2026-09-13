"""Report request logging model"""
from sqlalchemy import Column, Integer, String, ForeignKey
from src.data.db_context.base import LogBaseModel
from src.data.db_context.types import UUIDBinary

class LogReportRequestModel(LogBaseModel):
    __tablename__ = "log_report_request"
    
    report_type_id = Column(Integer, ForeignKey('report_type.id'), nullable=False)
    user_ip_address = Column(String(39), nullable=False)
    
    # Foreign keys
    user_id = Column(UUIDBinary, ForeignKey('user.id'), nullable=False)
