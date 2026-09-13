"""Course creation log repository - Insert only"""
from uuid import UUID

from sqlalchemy.orm import Session
from src.data.models.log_course_creation_model import LogCourseCreationModel
from src.data.repositories.base.base_repository import BaseRepository

class LogCourseCreationRepository(BaseRepository):
    """Repository for Course Creation logs - Insert only"""
    
    def __init__(self, session: Session):
        super().__init__(session, LogCourseCreationModel)
    
    async def log(
        self,
        name: str,
        total_seat_limit: int,
        workload: int,
        active: bool,
        user_ip_address: str,
        user_id: UUID
    ) -> LogCourseCreationModel:
        """Log a course creation"""
        log = LogCourseCreationModel(
            name=name,
            total_seat_limit=total_seat_limit,
            workload=workload,
            active=active,
            user_ip_address=user_ip_address,
            user_id=user_id
        )
        return await self.create(log)
