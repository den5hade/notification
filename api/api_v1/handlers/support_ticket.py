from fastapi import APIRouter, HTTPException, status
from typing import Dict
import logging

from schemas.notification import SupportTicketRequest
from services.send_email_service import email_service

support_ticket = APIRouter()

logger = logging.getLogger(__name__)

@support_ticket.post("/support-ticket", status_code=status.HTTP_200_OK, tags=["notifications"])
async def send_support_ticket_notification(request: SupportTicketRequest) -> Dict:
    """
    Send a support ticket notification email to the recipient.
    """
    try:
        logger.info(f"Processing support ticket notification for ticket {request.ticket_id}")
        
        # Validate request data
        if not request.ticket_id or not request.user_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing required fields: ticket_id and user_email are required"
            )
        
        # Send the support ticket notification email
        result = await email_service.send_notification_email(request)
        
        # Return appropriate response based on result
        if result["success"]:
            logger.info(f"Support ticket notification sent successfully for ticket {request.ticket_id}")
            return result
        else:
            logger.error(f"Failed to send support ticket notification: {result['message']}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result["message"]
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error processing support ticket {request.ticket_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred while processing support ticket notification"
        )
