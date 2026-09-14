from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.data.models.email_validation_model import EmailValidationModel
from src.data.repositories.base.base_repository import BaseRepository

class EmailValidationRepository(BaseRepository):
    '''Repository for e-mail validation'''
    def __init__(self, session: AsyncSession):
        super().__init__(session, EmailValidationModel)

    async def get_by_user_id(self, user_id: UUID) -> EmailValidationModel | None:
        stmt = select(EmailValidationModel).where(EmailValidationModel.user_id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_one(self, token: str, user_id: UUID) -> EmailValidationModel | None:
        stmt = select(EmailValidationModel).where(and_(
            EmailValidationModel.token == token,
            EmailValidationModel.user_id == user_id
        ))
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
