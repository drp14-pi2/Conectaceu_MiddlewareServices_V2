"""User activation log repository - Insert only"""
from typing import Optional
from uuid import UUID
from sqlalchemy.orm import Session
from src.data.models.log_user_activation_model import LogUserActivationModel
from src.data.repositories.base.base_repository import BaseRepository

class LogUserActivationRepository(BaseRepository):
    """Repository for User Activation logs - Insert only"""
    
    def __init__(self, session: Session):
        super().__init__(session, LogUserActivationModel)
    
    async def log(
        self,
        deactivation_reason: Optional[str],
        activated: bool,
        user_id: UUID,
        performed_by_user_id: UUID,
        performed_by_user_ip_address: str
    ) -> LogUserActivationModel:
        """Log a user activation/deactivation"""
        log = LogUserActivationModel(
            deactivation_reason=deactivation_reason,
            activated=activated,
            user_id=user_id,
            performed_by_user_id=performed_by_user_id,
            performed_by_user_ip_address=performed_by_user_ip_address
        )
        return await self.create(log)
