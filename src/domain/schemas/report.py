"""Report schemas"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel

class ReportRequest(BaseModel):
    report_type_id: int
    course_id: Optional[UUID] = None
    component_id: Optional[UUID] = None
    requested_by_user_id: UUID

class ReportResponse(BaseModel):
    report_type_id: int
    generated_at: datetime
    data: List[Dict[str, Any]]
