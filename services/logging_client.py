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

    def __init__(self, base_url: str = settings.logging_service_url):
        # if base_url is None:
        #     base_url = settings.logging_service_url
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
    
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()


# Global logging client instance
logging_client = LoggingClient()
