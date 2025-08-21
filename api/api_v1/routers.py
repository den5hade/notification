from fastapi import APIRouter

from .handlers.notification import notification_router
from .handlers.support_ticket import support_ticket


# Create main API v1 router
api_router = APIRouter()

# Include notification routes
api_router.include_router(
    notification_router,
    prefix="/notifications",
    tags=["notifications"]
)

# Include support ticket routes
api_router.include_router(
    support_ticket,
    prefix="/support-tickets",
    tags=["support-tickets"]
)
