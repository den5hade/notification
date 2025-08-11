from fastapi import APIRouter

from .handlers import notification_router, logs_router


# Create main API v1 router
api_router = APIRouter()

# Include notification routes
api_router.include_router(
    notification_router,
    prefix="/notifications",
    tags=["notifications"]
)

# Include logs routes
api_router.include_router(
    logs_router,
    prefix="/logs",
    tags=["logs"]
)