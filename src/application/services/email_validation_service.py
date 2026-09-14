from datetime import datetime, timedelta
from uuid import UUID, uuid4

from src.application.services.base_service import BaseService
from src.data.models.email_validation_model import EmailValidationModel
from src.data.models.user_model import UserModel
from src.data.repositories.email_validation_repository import EmailValidationRepository
from src.data.repositories.user_repository import UserRepository
from src.infrastructure.configuration.settings import settings
from src.infrastructure.handlers.datetime_handler import DateTimeHandler
from src.infrastructure.messaging.email.email_service import EmailService

class EmailValidationService(BaseService):
    '''Service for e-mail validation business logic'''
    def __init__(
        self,
        repository: EmailValidationRepository,
        user_repo: UserRepository,
        email_service: EmailService
    ):
        super().__init__(repository, 'email_validation')
        self.repository = repository
        self.user_repo = user_repo
        self.email_service = email_service

    async def request_email_validation(self, user_id: UUID) -> None:
        user: UserModel | None = await self.user_repo.get_by_id(user_id)

        if not user or not user.active:
            raise ValueError('Usuário não encontrado')

        if user.email_verified:
            raise ValueError('E-mail já verificado')

        if not user.email:
            raise ValueError('Usuário não possui e-mail')

        email_validation: EmailValidationModel = await self._create_update_email_validation(user.id)
        await self.repository.session.commit()
        email_content_html: str = self._get_email_validation_html(user.name, email_validation.token)
        await self.email_service.send_email(user.email, subject='Verificação de e-mail ConectaCEU', html_content=email_content_html)

    async def validate_email(self, token: str, user_id: UUID) -> None:
        email_validation: EmailValidationModel | None = await self.repository.get_one(token, user_id)

        if not email_validation:
            raise ValueError('Token inválido')

        if self._is_token_expired(email_validation.expires_at):
            raise ValueError('Token expirado')

        user: UserModel | None = await self.user_repo.get_by_id(email_validation.user_id)

        if not user or not user.active:
            raise ValueError('Usuário não encontrado')

        # Validates e-mail
        user.email_verified = True
        await self.user_repo.update(user)
        await self.repository.session.commit()

        # Deletes email_validation entry
        await self.repository.delete(email_validation.user_id)
        await self.repository.session.commit()

    # Private methods
    async def _create_update_email_validation(self, user_id: UUID):
        existing_validation: EmailValidationModel | None = await self.repository.get_by_user_id(user_id)

        if existing_validation:
            # If token expired, renew request
            if self._is_token_expired(existing_validation.expires_at):
                existing_validation.token = self._create_random_token()
                existing_validation.expires_at = self._get_new_expiration_date()

                return await self.repository.update(existing_validation)

            return existing_validation

        # Create validation if none found
        token: str = self._create_random_token()
        now: datetime = DateTimeHandler.now()
        expiration_date: datetime = self._get_new_expiration_date()
        email_validation:EmailValidationModel = EmailValidationModel(
            user_id=user_id,
            token=token,
            expires_at=expiration_date,
            created_at=now,
        )

        return await self.repository.create(email_validation)

    def _is_token_expired(self, expires_at: datetime) -> bool:
        return expires_at < DateTimeHandler.now();

    def _get_new_expiration_date(self) -> datetime:
        return DateTimeHandler.now() + timedelta(hours=settings.EMAIL_VALIDATION_TOKEN_EXPIRATION_HOURS)

    def _create_random_token(self) -> str:
        return f'{uuid4()}{uuid4()}'.replace('-', '').lower()

    def _get_email_validation_html(self, user_name: str, token: str):
        full_url: str = f'{settings.APP_API_URL}{settings.VALIDATE_EMAIL_VALIDATION_TOKEN_ENDPOINT}'.replace('{token}', token)
        user_first_name: str = user_name.split(' ')[0].capitalize()

        return f'''
            <html>
                <body style="font-family: Arial, sans-serif;">
                    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                        <h2 style="color: #333;">Verificação de e-mail ConectaCEU</h2>
                        <div style="background: #f9f9f9; padding: 20px; border-radius: 5px;">
                            <p style="white-space: pre-wrap;">Olá, {user_first_name}!</p>
                            <br/>
                            <p style="white-space: pre-wrap;">Uma validação foi pedida para seu endereço de e-mail.</p>
                            <p style="white-space: pre-wrap;">Se não foi você, favor desconsiderar esta mensagem. Se foi, <a href="{full_url}">clique aqui</a> para validar!</p>
                        </div>
                        <p style="color: #666; font-size: 12px; margin-top: 20px;">
                            Esta é uma mensagem automática do sistema ConectaCEU. Favor não responder.
                        </p>
                    </div>
                </body>
            </html>
        '''
