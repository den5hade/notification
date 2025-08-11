import asyncio
import json
import time
import logging
import re
from typing import Callable, Dict, Any, Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import StreamingResponse

from services.logging_client import logging_client, LogCreate
from core.config import settings


logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log all API requests and responses to the logging microservice."""

    def __init__(self, app, service_name: str = "notification-service"):
        super().__init__(app)
        self.service_name = service_name
        self.enabled = settings.enable_request_logging
        self.log_request_body = getattr(settings, 'log_request_body', True)
        self.log_response_body = getattr(settings, 'log_response_body', True)
        self.max_body_size = getattr(settings, 'max_log_body_size', 10000)

        # Paths to exclude from logging (health checks, metrics, etc.)
        self.excluded_paths = {
            "/health",
            "/metrics",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/favicon.ico",
            "/"
        }
        
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and log to logging microservice."""

        if not self.enabled:
            return await call_next(request)

        # Skip logging for excluded paths
        if request.url.path in self.excluded_paths:
            return await call_next(request)

        start_time = time.time()

        # Capture request data
        request_data = await self._capture_request_data(request)

        # Process the request
        response = await call_next(request)

        # Calculate processing time
        processing_time = int((time.time() - start_time) * 1000)  # Convert to milliseconds

        # Capture response data
        response_data = await self._capture_response_data(response)

        # Create log entry asynchronously (fire and forget)
        asyncio.create_task(self._log_request_response(
            request, response, request_data, response_data, processing_time
        ))

        return response
    
    async def _capture_request_data(self, request: Request) -> Dict[str, Any]:
        """Capture request data for logging."""
        data = {
            "method": request.method,
            "path": request.url.path,
            "query_params": dict(request.query_params) if request.query_params else None,
            "headers": dict(request.headers),
            "client_ip": self._get_client_ip(request),
            "user_agent": request.headers.get("user-agent"),
            "request_body": None
        }

        # Capture request body if enabled and content type is appropriate
        if self.log_request_body and self._should_log_body(request.headers.get("content-type")):
            try:
                body = await request.body()
                if body and len(body) <= self.max_body_size:
                    # Try to decode as JSON first, then as text
                    try:
                        body_json = json.loads(body.decode('utf-8'))
                        # Mask sensitive fields in JSON body
                        masked_body = self._mask_sensitive_data(body_json)
                        data["request_body"] = json.dumps(masked_body)
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        try:
                            body_text = body.decode('utf-8')
                            # Mask sensitive data in text body (form data, etc.)
                            data["request_body"] = self._mask_sensitive_text(body_text)
                        except UnicodeDecodeError:
                            data["request_body"] = f"<binary data: {len(body)} bytes>"
                elif len(body) > self.max_body_size:
                    data["request_body"] = f"<body too large: {len(body)} bytes>"
            except Exception as e:
                data["request_body"] = f"<error reading body: {str(e)}>"

        return data

    async def _capture_response_data(self, response: Response) -> Dict[str, Any]:
        """Capture response data for logging."""
        data = {
            "status_code": response.status_code,
            "response_body": None
        }

        # Capture response body if enabled
        if self.log_response_body and hasattr(response, 'body'):
            try:
                if isinstance(response, StreamingResponse):
                    # For streaming responses, we can't easily capture the body
                    data["response_body"] = "<streaming response>"
                else:
                    body = response.body
                    if body and len(body) <= self.max_body_size:
                        # Try to decode as JSON first, then as text
                        try:
                            # Convert body to bytes if it's not already
                            body_bytes = body if isinstance(body, bytes) else bytes(body)
                            response_json = json.loads(body_bytes.decode('utf-8'))
                            # Mask sensitive fields in JSON response (like tokens)
                            masked_response = self._mask_sensitive_data(response_json)
                            data["response_body"] = json.dumps(masked_response)
                        except (json.JSONDecodeError, UnicodeDecodeError):
                            try:
                                body_bytes = body if isinstance(body, bytes) else bytes(body)
                                response_text = body_bytes.decode('utf-8')
                                # Mask sensitive data in text response
                                data["response_body"] = self._mask_sensitive_text(response_text)
                            except UnicodeDecodeError:
                                data["response_body"] = f"<binary data: {len(body)} bytes>"
                    elif len(body) > self.max_body_size:
                        data["response_body"] = f"<body too large: {len(body)} bytes>"
            except Exception as e:
                data["response_body"] = f"<error reading response body: {str(e)}>"

        return data

    async def _log_request_response(
        self,
        request: Request,
        response: Response,
        request_data: Dict[str, Any],
        response_data: Dict[str, Any],
        processing_time: int
    ):
        """Send log entry to the logger service."""
        try:
            # Filter sensitive headers
            headers = self._filter_sensitive_headers(request_data["headers"])

            log_entry = LogCreate(
                service_name=self.service_name,
                method=request_data["method"],
                path=request_data["path"],
                query_params=request_data["query_params"],
                request_body=request_data["request_body"],
                response_body=response_data["response_body"],
                status_code=response_data["status_code"],
                processing_time=processing_time,
                client_ip=request_data["client_ip"],
                user_agent=request_data["user_agent"],
                headers=headers
            )

            # Send to logger service (non-blocking)
            await logging_client.create_log_entry(log_entry)

        except Exception as e:
            # Log the error but don't fail the request
            logger.error(f"Failed to log request: {str(e)}")

    def _get_client_ip(self, request: Request) -> Optional[str]:
        """Extract client IP from request headers."""
        # Check for forwarded headers first (for reverse proxies)
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip

        # Fall back to direct client IP
        if hasattr(request, "client") and request.client:
            return request.client.host

        return None
    
    def _should_log_body(self, content_type: Optional[str]) -> bool:
        """Determine if we should log the request/response body based on content type."""
        if not content_type:
            return False

        # Log JSON and text content types
        loggable_types = [
            "application/json",
            "application/x-www-form-urlencoded",
            "text/plain",
            "text/html",
            "text/xml",
            "application/xml"
        ]

        return any(content_type.startswith(t) for t in loggable_types)

    def _filter_sensitive_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
        """Filter out sensitive headers from logging."""
        sensitive_headers = {
            "authorization",
            "cookie",
            "x-api-key",
            "x-auth-token",
            "x-access-token"
        }

        filtered = {}
        for key, value in headers.items():
            if key.lower() in sensitive_headers:
                filtered[key] = "<redacted>"
            else:
                filtered[key] = value

        return filtered
    
    def _mask_sensitive_data(self, data: Any) -> Any:
        """Recursively mask sensitive data in JSON objects."""
        if isinstance(data, dict):
            masked_data = {}
            for key, value in data.items():
                if self._is_sensitive_field(key):
                    masked_data[key] = self._mask_value(value)
                elif isinstance(value, (dict, list)):
                    masked_data[key] = self._mask_sensitive_data(value)
                else:
                    masked_data[key] = value
            return masked_data
        elif isinstance(data, list):
            return [self._mask_sensitive_data(item) for item in data]
        else:
            return data

    def _is_sensitive_field(self, field_name: str) -> bool:
        """Check if a field name contains sensitive data."""
        sensitive_fields = {
            # Password related
            "password", "passwd", "pwd", "pass", "passphrase",
            "confirm_password", "new_password", "old_password", "current_password",
            "password_confirmation", "password_confirm", "repeat_password",

            # Authentication tokens
            "token", "access_token", "refresh_token", "auth_token", "bearer_token",
            "jwt", "jwt_token", "session_token", "csrf_token", "xsrf_token",

            # API keys and secrets
            "secret", "api_key", "apikey", "api_secret", "client_secret",
            "private_key", "public_key", "encryption_key", "signing_key",

            # Authentication
            "auth", "authorization", "credential", "credentials",
            "session", "session_id", "cookie", "cookies",

            # Personal information
            "pin", "ssn", "social_security", "social_security_number",
            "credit_card", "card_number", "card_num", "cvv", "cvc", "cvv2",
            "bank_account", "account_number", "routing_number",

            # Other sensitive data
            "otp", "verification_code", "reset_code", "activation_code",
            "security_question", "security_answer", "backup_codes"
        }

        field_lower = field_name.lower()
        return any(sensitive in field_lower for sensitive in sensitive_fields)

    def _mask_value(self, value: Any) -> Any:
        """Mask a sensitive value."""
        if value is None:
            return None

        value_str = str(value)
        if len(value_str) <= 2:
            return "***"
        elif len(value_str) <= 6:
            return value_str[0] + "*" * (len(value_str) - 2) + value_str[-1]
        else:
            return value_str[:2] + "*" * (len(value_str) - 4) + value_str[-2:]

    def _mask_sensitive_text(self, text: str) -> str:
        """Mask sensitive data in text format (form data, query strings, etc.)."""
        # Common patterns for form data and query strings
        patterns = [
            # password=value or password:value
            (r'(password[=:]\s*)([^&\s\n\r]+)', r'\1***'),
            (r'(passwd[=:]\s*)([^&\s\n\r]+)', r'\1***'),
            (r'(pwd[=:]\s*)([^&\s\n\r]+)', r'\1***'),
            # token=value or token:value
            (r'(token[=:]\s*)([^&\s\n\r]+)', r'\1***'),
            (r'(secret[=:]\s*)([^&\s\n\r]+)', r'\1***'),
            (r'(key[=:]\s*)([^&\s\n\r]+)', r'\1***'),
            # API key patterns
            (r'(api[_-]?key[=:]\s*)([^&\s\n\r]+)', r'\1***'),
            (r'(access[_-]?token[=:]\s*)([^&\s\n\r]+)', r'\1***'),
            # Credit card patterns (basic)
            (r'(\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4})', r'****-****-****-****'),
        ]

        masked_text = text
        for pattern, replacement in patterns:
            masked_text = re.sub(pattern, replacement, masked_text, flags=re.IGNORECASE)

        return masked_text


class RequestLoggingConfig:
    """Configuration class for request logging."""

    def __init__(
        self,
        service_name: str = "notification-service",
        enabled: bool = True,
        log_request_body: bool = True,
        log_response_body: bool = True,
        max_body_size: int = 10000,
        excluded_paths: Optional[set] = None
    ):
        self.service_name = service_name
        self.enabled = enabled
        self.log_request_body = log_request_body
        self.log_response_body = log_response_body
        self.max_body_size = max_body_size
        self.excluded_paths = excluded_paths or {
            "/health", "/metrics", "/docs", "/redoc", "/openapi.json", "/favicon.ico", "/"
        }
