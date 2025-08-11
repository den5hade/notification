from enum import Enum
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class NotificationTask(str, Enum):
    """Enum for notification task types."""
    EMAIL_VERIFICATION = "email_verification"
    CHANGE_PASSWORD = "change_password"


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


class NotificationResponse(BaseModel):
    """Schema for notification response."""
    success: bool = Field(..., description="Whether the notification was sent successfully")
    message: str = Field(..., description="Response message")
    email: Optional[str] = Field(None, description="Email address that was notified")
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
