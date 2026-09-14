"""Email service for sending notifications with attachments"""
from typing import Optional
import smtplib
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

from src.infrastructure.configuration.settings import settings

class EmailService:
    """Service for sending emails with optional attachments"""
    
    def __init__(self):
        self.smtp_host = settings.EMAIL_SMTP_HOST
        self.smtp_port = settings.EMAIL_SMTP_PORT
        self.smtp_user = settings.EMAIL_SMTP_USER
        self.smtp_password = settings.EMAIL_SMTP_PASSWORD
        self.from_email = settings.EMAIL_FROM_EMAIL
        self.from_name = settings.EMAIL_FROM_NAME
    
    async def send_broadcast_email(
        self,
        to_email: str,
        subject: str,
        message: str,
        document_1_base64: Optional[str] = None,
        document_2_base64: Optional[str] = None,
        document_1_name: str = "documento_1",
        document_2_name: str = "documento_2"
    ) -> bool:
        """
        Send broadcast email with optional documents.
        
        Args:
            to_email: Recipient email
            subject: Email subject
            message: Email body (HTML)
            document_1_base64: Optional first document
            document_2_base64: Optional second document
            document_1_name: Name for first document
            document_2_name: Name for second document
            
        Returns:
            True if sent successfully
        """
        try:
            msg = MIMEMultipart()
            msg["Subject"] = subject
            msg["From"] = f"{self.from_name} <{self.from_email}>"
            msg["To"] = to_email
            
            # Add HTML body
            msg.attach(MIMEText(message, "html"))
            
            # Attach documents
            if document_1_base64:
                self._attach_base64_document(msg, document_1_base64, document_1_name)
            
            if document_2_base64:
                self._attach_base64_document(msg, document_2_base64, document_2_name)
            
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                if self.smtp_user and self.smtp_password:
                    server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            
            return True
        except Exception as e:
            print(f"Failed to send email: {e}")
            return False
    
    def _attach_base64_document(self, msg: MIMEMultipart, base64_content: str, fileNameWithExtension: str) -> None:
        """Attach a base64 document to an email"""
        try:
            # Determine file type
            mime_type = "application/octet-stream"
            if base64_content.startswith("data:"):
                header, base64_content = base64_content.split(",", 1)
                mime_type = header.split(":")[1].split(";")[0]
            
            # Decode base64
            file_data = base64.b64decode(base64_content)
            
            # Determine extension from mime type
            splitFileName = fileNameWithExtension.split('.')
            fileName = splitFileName[0]
            ext = (splitFileName[1] if len(splitFileName) == 2 else self._get_extension_from_mime(mime_type)).replace('.', '')
            
            # Create attachment
            part = MIMEBase("application", "octet-stream")
            part.set_payload(file_data)
            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition",
                f"attachment; filename={fileName}.{ext}"
            )
            
            msg.attach(part)
        except Exception as e:
            print(f"Failed to attach document: {e}")
    
    def _get_extension_from_mime(self, mime_type: str) -> str:
        """Get file extension from MIME type"""
        extensions = {
            "image/png": ".png",
            "image/jpeg": ".jpg",
            "image/jpg": ".jpg",
            "application/pdf": ".pdf",
            "application/msword": ".doc",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
        }
        return extensions.get(mime_type, ".bin")
    
    async def send_password_reset_email(
        self,
        to_email: str,
        reset_token: str,
        frontend_url: str
    ) -> bool:
        """Send password reset email"""
        reset_link = f"{frontend_url}/reset-password?token={reset_token}"
        
        subject = "ConectaCEU - Recuperação de Senha"
        
        html_content = f"""
        <html>
            <body>
                <h2>Recuperação de Senha</h2>
                <p>Olá,</p>
                <p>Recebemos uma solicitação para redefinir sua senha.</p>
                <p>Clique no link abaixo para criar uma nova senha:</p>
                <p><a href="{reset_link}">{reset_link}</a></p>
                <p>Este link expira em 1 hora.</p>
                <p>Se você não solicitou esta alteração, ignore este email.</p>
                <p>Atenciosamente,<br>Equipe ConectaCEU</p>
            </body>
        </html>
        """
        
        return await self.send_email(to_email, subject, html_content)
    
    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str
    ) -> bool:
        """Send simple email without attachments"""
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{self.from_name} <{self.from_email}>"
            msg["To"] = to_email
            msg.attach(MIMEText(html_content, "html"))
            
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                if self.smtp_user and self.smtp_password:
                    server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            
            return True
        except Exception as e:
            print(f"Failed to send email: {e}")
            return False