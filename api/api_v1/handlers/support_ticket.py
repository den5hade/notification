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
        
        # Send both confirmation email to user and notification email to support team
        result = await email_service.send_support_ticket_emails(request)
        
        # Return appropriate response based on result
        if result["success"]:
            logger.info(f"Support ticket emails sent successfully for ticket {request.ticket_id}")
            return {
                "success": True,
                "message": "Support ticket processed successfully - confirmation sent to user and notification sent to support team",
                "ticket_id": request.ticket_id,
                "user_email_result": result.get("user_email_result"),
                "support_email_result": result.get("support_email_result")
            }
        else:
            # Check which emails failed and provide appropriate error message
            failed_parts = []
            if result.get("user_email_result") and not result["user_email_result"]["success"]:
                failed_parts.append("user confirmation email")
            if result.get("support_email_result") and not result["support_email_result"]["success"]:
                failed_parts.append("support team notification")

            error_message = f"Failed to send: {', '.join(failed_parts)}"
            logger.error(f"Support ticket email failure for ticket {request.ticket_id}: {error_message}")

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=error_message
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error processing support ticket {request.ticket_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred while processing support ticket notification"
        )
