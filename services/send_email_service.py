import os
import logging
from typing import Dict, Any
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path

import aiosmtplib
from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from core.config import settings
from schemas.notification import NotificationRequest, NotificationTask


logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails using Gmail SMTP."""
    
    def __init__(self):
        """Initialize the email service with Jinja2 template environment."""
        template_path = Path(settings.template_dir)
        if not template_path.exists():
            raise FileNotFoundError(f"Template directory not found: {template_path}")
        
        self.jinja_env = Environment(
            loader=FileSystemLoader(template_path),
            autoescape=True
        )
        
    async def send_notification_email(self, request: NotificationRequest) -> Dict[str, Any]:
        """
        Send notification email based on the request.
        
        Args:
            request: NotificationRequest containing email details
            
        Returns:
            Dict containing success status and message
        """
        try:
            # Get the appropriate template based on task type
            template_name = self._get_template_name(request.task)
            
            # Render the email content
            html_content = await self._render_template(template_name, {
                "user_name": request.user_name,
                "link": request.link
            })
            
            # Create and send the email
            await self._send_email(
                to_email=request.email,
                subject=request.subject,
                html_content=html_content
            )
            
            logger.info(f"Email sent successfully to {request.email} for task {request.task}")
            return {
                "success": True,
                "message": "Email sent successfully",
                "email": request.email,
                "task": request.task
            }
            
        except Exception as e:
            logger.error(f"Failed to send email to {request.email}: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to send email: {str(e)}",
                "email": request.email,
                "task": request.task
            }
    
    def _get_template_name(self, task: NotificationTask) -> str:
        """Get template filename based on notification task."""
        template_mapping = {
            NotificationTask.EMAIL_VERIFICATION: "email_verification.html",
            NotificationTask.CHANGE_PASSWORD: "change_password.html"
        }
        return template_mapping.get(task, "email_verification.html")
    
    async def _render_template(self, template_name: str, context: Dict[str, Any]) -> str:
        """
        Render HTML template with given context.
        
        Args:
            template_name: Name of the template file
            context: Template context variables
            
        Returns:
            Rendered HTML content
        """
        try:
            template = self.jinja_env.get_template(template_name)
            return template.render(**context)
        except TemplateNotFound:
            logger.error(f"Template not found: {template_name}")
            raise
        except Exception as e:
            logger.error(f"Error rendering template {template_name}: {str(e)}")
            raise
    
    async def _send_email(self, to_email: str, subject: str, html_content: str) -> None:
        """
        Send email using Gmail SMTP.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML content of the email
        """
        # Create message
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = f"{settings.from_name} <{settings.from_email}>"
        message["To"] = to_email
        
        # Add HTML content
        html_part = MIMEText(html_content, "html")
        message.attach(html_part)
        
        # Send email
        try:
            # Prepare connection parameters
            connection_params = {
                "hostname": settings.smtp_server,
                "port": settings.smtp_port,
            }

            # Add authentication if credentials are provided
            if settings.smtp_username and settings.smtp_password:
                connection_params["username"] = settings.smtp_username
                connection_params["password"] = settings.smtp_password

            # Configure SSL/TLS based on port and settings
            if settings.smtp_port == 465:
                # Use SSL for port 465 (implicit SSL)
                connection_params["use_tls"] = True
                connection_params["start_tls"] = False
            elif settings.smtp_port == 587:
                # Use STARTTLS for port 587
                connection_params["start_tls"] = True
                connection_params["use_tls"] = False
            else:
                # For other ports (like MailHog on 1025), use plain connection
                connection_params["use_tls"] = False
                connection_params["start_tls"] = False

            await aiosmtplib.send(message, **connection_params)

        except Exception as e:
            logger.error(f"SMTP error: {str(e)}")
            raise


# Global email service instance
email_service = EmailService()
