import json
import time
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

import httpx
from pydantic import BaseModel, Field

from core.config import settings


logger = logging.getLogger(__name__)


class LogCreate(BaseModel):
    """Schema for creating a new log entry (from logging microservice)."""
    service_name: str = Field(..., max_length=50)
    method: str = Field(..., max_length=10)
    path: str = Field(..., max_length=255)
    query_params: Optional[Dict[str, Any]] = None
    request_body: Optional[str] = None
    response_body: Optional[str] = None
    status_code: int
    processing_time: int = Field(..., description="Processing time in milliseconds")
    client_ip: Optional[str] = Field(None, max_length=50)
    user_agent: Optional[str] = Field(None, max_length=255)
    headers: Optional[Dict[str, Any]] = None


class LogRead(BaseModel):
    """Schema for reading log entries (from logging microservice)."""
    id: int
    service_name: str
    method: str
    path: str
    query_params: Optional[Dict[str, Any]] = None
    request_body: Optional[str] = None
    response_body: Optional[str] = None
    status_code: int
    processing_time: int
    client_ip: Optional[str] = None
    user_agent: Optional[str] = None
    headers: Optional[Dict[str, Any]] = None
    timestamp: datetime


class LoggingClient:
    """Client for interacting with the logging microservice."""

    def __init__(self, base_url: str = None):
        if base_url is None:
            base_url = settings.logging_service_url
        self.base_url = base_url.rstrip("/")
        self.client = httpx.AsyncClient(timeout=5.0)
        
    async def create_log_entry(self, log_data: LogCreate) -> Optional[LogRead]:
        """Create a new log entry in the logging microservice."""
        try:
            response = await self.client.post(
                f"{self.base_url}/api/v1/logs/",
                json=log_data.model_dump(),
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                return LogRead(**response.json())
            else:
                logger.error(f"Failed to create log entry: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating log entry: {str(e)}")
            return None
    
    async def create_bulk_logs(self, logs: List[LogCreate]) -> Optional[List[LogRead]]:
        """Create multiple log entries in a single request."""
        try:
            response = await self.client.post(
                f"{self.base_url}/api/v1/logs/bulk",
                json=[log.model_dump() for log in logs],
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                return [LogRead(**log_data) for log_data in response.json()]
            else:
                logger.error(f"Failed to create bulk logs: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating bulk logs: {str(e)}")
            return None
    
    async def get_logs(
        self,
        skip: int = 0,
        limit: int = 100,
        service_name: Optional[str] = None,
        method: Optional[str] = None,
        status_code: Optional[int] = None,
        client_ip: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Optional[List[LogRead]]:
        """Retrieve log entries with optional filtering."""
        try:
            params = {"skip": skip, "limit": limit}
            
            # Add optional filters
            if service_name:
                params["service_name"] = service_name
            if method:
                params["method"] = method
            if status_code:
                params["status_code"] = status_code
            if client_ip:
                params["client_ip"] = client_ip
            if start_date:
                params["start_date"] = start_date.isoformat()
            if end_date:
                params["end_date"] = end_date.isoformat()
            
            response = await self.client.get(
                f"{self.base_url}/api/v1/logs/",
                params=params
            )
            
            if response.status_code == 200:
                return [LogRead(**log_data) for log_data in response.json()]
            else:
                logger.error(f"Failed to get logs: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting logs: {str(e)}")
            return None
    
    async def get_log_by_id(self, log_id: int) -> Optional[LogRead]:
        """Get a specific log entry by its ID."""
        try:
            response = await self.client.get(f"{self.base_url}/api/v1/logs/{log_id}")
            
            if response.status_code == 200:
                return LogRead(**response.json())
            else:
                logger.error(f"Failed to get log {log_id}: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting log {log_id}: {str(e)}")
            return None
    
    async def get_total_logs_count(
        self,
        service_name: Optional[str] = None,
        method: Optional[str] = None,
        status_code: Optional[int] = None,
        client_ip: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Optional[int]:
        """Get total count of logs matching the filters."""
        try:
            params = {}
            
            # Add optional filters
            if service_name:
                params["service_name"] = service_name
            if method:
                params["method"] = method
            if status_code:
                params["status_code"] = status_code
            if client_ip:
                params["client_ip"] = client_ip
            if start_date:
                params["start_date"] = start_date.isoformat()
            if end_date:
                params["end_date"] = end_date.isoformat()
            
            response = await self.client.get(
                f"{self.base_url}/api/v1/logs/count/total",
                params=params
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("total_count", 0)
            else:
                logger.error(f"Failed to get logs count: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting logs count: {str(e)}")
            return None
    
    async def get_services_stats(self) -> Optional[Dict[str, Any]]:
        """Get statistics about all logged services."""
        try:
            response = await self.client.get(f"{self.base_url}/api/v1/logs/stats/services")
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to get services stats: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting services stats: {str(e)}")
            return None
    
    async def cleanup_old_logs(self, days_old: int = 30) -> Optional[Dict[str, Any]]:
        """Delete log entries older than the specified number of days."""
        try:
            response = await self.client.delete(
                f"{self.base_url}/api/v1/logs/cleanup",
                params={"days_old": days_old}
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to cleanup logs: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error cleaning up logs: {str(e)}")
            return None
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()


# Global logging client instance
logging_client = LoggingClient()
