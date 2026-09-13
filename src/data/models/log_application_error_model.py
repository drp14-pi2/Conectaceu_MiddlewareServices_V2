"""Application error logging model """
from sqlalchemy import Column, Text
from src.data.db_context.base import LogBaseModel

class LogApplicationErrorModel(LogBaseModel):
    __tablename__ = "log_application_error"
    
    exception = Column(Text, nullable=False)
    stacktrace = Column(Text, nullable=False)
