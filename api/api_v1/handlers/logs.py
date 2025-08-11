import logging
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, status, Query
from fastapi.responses import JSONResponse

from services.logging_client import logging_client, LogRead


logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/",
    response_model=List[LogRead],
    status_code=status.HTTP_200_OK,
    summary="Get logs from logging service",
    description="Retrieve logs from the logging microservice with optional filtering"
)
async def get_logs(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, le=1000, description="Maximum number of records to return"),
    service_name: Optional[str] = Query(None, description="Filter by service name"),
    method: Optional[str] = Query(None, description="Filter by HTTP method"),
    status_code: Optional[int] = Query(None, description="Filter by status code"),
    client_ip: Optional[str] = Query(None, description="Filter by client IP"),
    start_date: Optional[datetime] = Query(None, description="Filter logs after this date"),
    end_date: Optional[datetime] = Query(None, description="Filter logs before this date")
) -> List[LogRead]:
    """
    Get logs from the logging microservice.
    
    Supports filtering by service name, HTTP method, status code, client IP,
    and date range. Results are paginated.
    """
    try:
        logs = await logging_client.get_logs(
            skip=skip,
            limit=limit,
            service_name=service_name,
            method=method,
            status_code=status_code,
            client_ip=client_ip,
            start_date=start_date,
            end_date=end_date
        )
        
        if logs is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Logging service is unavailable"
            )
        
        return logs
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting logs: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred while retrieving logs"
        )


@router.get(
    "/{log_id}",
    response_model=LogRead,
    status_code=status.HTTP_200_OK,
    summary="Get specific log entry",
    description="Get a specific log entry by its ID"
)
async def get_log_by_id(log_id: int) -> LogRead:
    """
    Get a specific log entry by its ID.
    
    Args:
        log_id: The ID of the log entry to retrieve
        
    Returns:
        LogRead: The log entry data
        
    Raises:
        HTTPException: If log not found or service unavailable
    """
    try:
        log_entry = await logging_client.get_log_by_id(log_id)
        
        if log_entry is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Log entry with ID {log_id} not found"
            )
        
        return log_entry
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting log {log_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred while retrieving log"
        )


@router.get(
    "/count/total",
    status_code=status.HTTP_200_OK,
    summary="Get total logs count",
    description="Get the total count of log entries matching the filters"
)
async def get_total_logs_count(
    service_name: Optional[str] = Query(None, description="Filter by service name"),
    method: Optional[str] = Query(None, description="Filter by HTTP method"),
    status_code: Optional[int] = Query(None, description="Filter by status code"),
    client_ip: Optional[str] = Query(None, description="Filter by client IP"),
    start_date: Optional[datetime] = Query(None, description="Filter logs after this date"),
    end_date: Optional[datetime] = Query(None, description="Filter logs before this date")
):
    """
    Get total count of logs matching the filters.
    
    Returns:
        JSON response with total count
    """
    try:
        total_count = await logging_client.get_total_logs_count(
            service_name=service_name,
            method=method,
            status_code=status_code,
            client_ip=client_ip,
            start_date=start_date,
            end_date=end_date
        )
        
        if total_count is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Logging service is unavailable"
            )
        
        return JSONResponse(content={"total_count": total_count})
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting logs count: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred while getting logs count"
        )


@router.get(
    "/stats/services",
    status_code=status.HTTP_200_OK,
    summary="Get service statistics",
    description="Get statistics about all logged services"
)
async def get_services_stats():
    """
    Get statistics about all logged services.
    
    Returns:
        JSON response with service statistics
    """
    try:
        stats = await logging_client.get_services_stats()
        
        if stats is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Logging service is unavailable"
            )
        
        return JSONResponse(content=stats)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting services stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred while getting services stats"
        )


@router.delete(
    "/cleanup",
    status_code=status.HTTP_200_OK,
    summary="Cleanup old logs",
    description="Delete log entries older than the specified number of days"
)
async def cleanup_old_logs(
    days_old: int = Query(30, ge=1, description="Delete logs older than this many days")
):
    """
    Delete log entries older than the specified number of days.
    
    Args:
        days_old: Number of days - logs older than this will be deleted
        
    Returns:
        JSON response with cleanup results
    """
    try:
        result = await logging_client.cleanup_old_logs(days_old)
        
        if result is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Logging service is unavailable"
            )
        
        return JSONResponse(content=result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cleaning up logs: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred while cleaning up logs"
        )
