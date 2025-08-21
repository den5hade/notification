from enum import Enum
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class NotificationTask(str, Enum):
    """Enum for notification task types."""
    EMAIL_VERIFICATION = "email_verification"
    CHANGE_PASSWORD = "change_password"
    SUPPORT_TICKET = "support_ticket"


class SupportTicketCategory(str, Enum):
    """Categories for support ticket classification"""
    LOGIN = "login"
    PRODUCT_SERVICE = "product service"
    SEARCH = "search"
    OTHER = "other"
    STORE_SERVICE = "store service"


class NotificationRequest(BaseModel):
    """Schema for notification request from registration microservice."""
    email: EmailStr = Field(..., description="Recipient email address")
    task: NotificationTask = Field(..., description="Type of notification task")
    link: str = Field(..., description="Action link to include in the email")
    user_name: str = Field(..., description="Name of the user")
    subject: str = Field(..., description="Email subject line")

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "task": "email_verification",
                "link": "http://localhost:8000/api/v1/auth/verify-email?token=8d9a1b50-e4f1-47b2-bd3b-37245db5c9db",
                "user_name": "User Name",
                "subject": "Please verify your email address"
            }
        }


class SupportTicketRequest(NotificationRequest):
    """Schema for support ticket notification requests."""
    user_email: EmailStr = Field(..., description="Submitter's email for responses")
    category: SupportTicketCategory = Field(..., description="Support issue category")
    ticket_id: str = Field(..., description="Unique support ticket identifier")
    priority: str = Field(..., description="Urgency level [High/Medium/Low]")
    description: str = Field(..., description="Detailed issue description")
    due_date: Optional[str] = Field(None, description="Expected resolution date/time")

    class Config:
        json_schema_extra = {
            "example": {
                "email": "support@example.com",
                "task": "support_ticket",
                "link": "https://portal.example.com/ticket/12345",
                "user_name": "Support Team",
                "subject": "New Support Ticket Created",
                "user_email": "requester@example.com",
                "category": "login",
                "ticket_id": "TICKET-12345",
                "priority": "High",
                "description": "User unable to log in after password reset",
                "due_date": "2023-06-20T18:00:00Z"
            }
        }


class NotificationResponse(BaseModel):
    """Schema for notification response."""
    success: bool = Field(..., description="Whether the notification was sent successfully")
    message: str = Field(..., description="Response message")
    email: Optional[EmailStr] = Field(None, description="Email address that was notified")
    task: Optional[NotificationTask] = Field(None, description="Task that was processed")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Email sent successfully",
                "email": "user@example.com",
                "task": "email_verification"
            }
        }
