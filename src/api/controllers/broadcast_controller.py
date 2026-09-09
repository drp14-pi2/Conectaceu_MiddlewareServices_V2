"""Broadcast message controller"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from src.api.dependencies.auth_dependencies import get_current_active_user, require_permission
from src.application.services.broadcast_service import BroadcastService
from src.data.repositories.class_repository import ClassRepository
from src.data.repositories.course_component_repository import CourseComponentRepository
from src.data.repositories.user_repository import UserRepository
from src.data.repositories.user_course_repository import UserCourseRepository
from src.data.repositories.log_broadcast_message_repository import LogBroadcastMessageRepository
from src.domain.constants.permission_types import PermissionTypes
from src.domain.schemas.broadcast_message import BroadcastMessageCreate
from src.domain.schemas.user import User
from src.infrastructure.messaging.email.email_service import EmailService
from src.infrastructure.messaging.sms.sms_service import SmsService
from src.infrastructure.messaging.whatsapp.whatsapp_service import WhatsAppService
from src.data.db_context.database import get_db

router = APIRouter(
    prefix="/broadcast",
    tags=["Broadcasts"],
    dependencies=[Depends(get_current_active_user)]
)

def get_broadcast_service(db: Session = Depends(get_db)) -> BroadcastService:
    """Dependency injection for BroadcastService"""
    user_repo = UserRepository(db)
    user_course_repo = UserCourseRepository(db)
    log_repo = LogBroadcastMessageRepository(db)
    component_repo = CourseComponentRepository(db),
    class_repo = ClassRepository(db),
    email_service = EmailService()
    sms_service = SmsService()
    whatsapp_service = WhatsAppService()
    
    return BroadcastService(
        user_repo,
        user_course_repo,
        log_repo,
        component_repo,
        class_repo,
        email_service,
        sms_service,
        whatsapp_service
    )


@router.post("/", status_code=status.HTTP_200_OK)
async def send_broadcast(
    request: Request,
    dto: BroadcastMessageCreate,
    current_user: User = Depends(require_permission(PermissionTypes.SEND_BROADCAST_MESSAGE)),
    service: BroadcastService = Depends(get_broadcast_service)
):
    """
    Send a broadcast message via selected channels.
    Requires: send_broadcast_message permission (Admin/Secretary only).
    """
    try:
        user_ip: str = request.client.host if request.client else "unknown"

        return await service.send_broadcast(dto, current_user.id, user_ip)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
