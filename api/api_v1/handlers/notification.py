import logging
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse

from schemas.notification import NotificationRequest, NotificationResponse
from services.send_email_service import email_service


logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/send",
    response_model=NotificationResponse,
    status_code=status.HTTP_200_OK,
    summary="Send notification email",
    description="Send notification email based on the task type (email_verification or change_password)"
)
async def send_notification(request: NotificationRequest) -> NotificationResponse:
    """
    Send notification email.
    
    This endpoint accepts notification requests from other microservices
    and sends appropriate emails based on the task type.
    
    Args:
        request: NotificationRequest containing email details
        
    Returns:
        NotificationResponse with success status and details
        
    Raises:
        HTTPException: If email sending fails
    """
    try:
        logger.info(f"Received notification request for {request.email} with task {request.task}")
        
        # Send the email using the email service
        result = await email_service.send_notification_email(request)
        
        # Create response
        response = NotificationResponse(
            success=result["success"],
            message=result["message"],
            email=result.get("email"),
            task=result.get("task")
        )
        
        if not result["success"]:
            logger.error(f"Failed to send notification: {result['message']}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result["message"]
            )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in send_notification: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred while sending notification"
        )


@router.get(
    "/health",
    status_code=status.HTTP_200_OK,
    summary="Health check",
    description="Check if the notification service is healthy"
)
async def health_check():
    """
    Health check endpoint.
    
    Returns:
        JSON response indicating service health
    """
    return JSONResponse(
        content={
            "status": "healthy",
            "service": "notification",
            "message": "Notification service is running"
        }
    )
