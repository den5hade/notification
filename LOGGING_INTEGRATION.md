# Logging Integration

The notification microservice is now integrated with your logging microservice running on `http://0.0.0.0:8020`.

## Features

### 🔄 Automatic Request Logging
- **Middleware**: All API requests and responses are automatically logged
- **Enhanced Security**: Comprehensive sensitive data filtering with 40+ field patterns
- **Smart Masking**: Partial value masking instead of complete redaction
- **Content-Type Aware**: Only logs appropriate content types (JSON, form data, text)
- **Size Limits**: Configurable body size limits to prevent huge logs
- **Performance**: Processing time is tracked for each request
- **Client Info**: IP addresses and user agents are captured

### 📊 Logging API Endpoints
The notification service now provides endpoints to query logs:

- `GET /api/v1/logs/` - Get logs with filtering and pagination
- `GET /api/v1/logs/{log_id}` - Get specific log entry
- `GET /api/v1/logs/count/total` - Get total count of logs
- `GET /api/v1/logs/stats/services` - Get service statistics
- `DELETE /api/v1/logs/cleanup` - Cleanup old logs

### 🛠️ Direct Client Access
- **LoggingClient**: Direct programmatic access to logging service
- **Async Support**: All operations are asynchronous
- **Error Handling**: Graceful handling of logging service unavailability

## Configuration

Add these settings to your `.env` file:

```env
# Logging Service Settings
LOGGING_SERVICE_URL=http://0.0.0.0:8020
ENABLE_REQUEST_LOGGING=true
LOG_REQUEST_BODY=true
LOG_RESPONSE_BODY=true
MAX_LOG_BODY_SIZE=10000
```

### Configuration Options

- `ENABLE_REQUEST_LOGGING`: Enable/disable all request logging (default: true)
- `LOG_REQUEST_BODY`: Control whether request bodies are logged (default: true)
- `LOG_RESPONSE_BODY`: Control whether response bodies are logged (default: true)
- `MAX_LOG_BODY_SIZE`: Maximum body size to log in bytes (default: 10000)

## Usage Examples

### 1. Automatic Logging (Middleware)
All API requests are automatically logged when `ENABLE_REQUEST_LOGGING=true`:

```bash
# This request will be automatically logged
curl -X POST http://localhost:8030/api/v1/notifications/send \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "task": "email_verification",
    "link": "http://localhost:8030/verify?token=123",
    "user_name": "Test User",
    "subject": "Verify Email"
  }'
```

### 2. Query Logs via API
```bash
# Get recent logs for notification service
curl "http://localhost:8030/api/v1/logs/?service_name=notification-service&limit=10"

# Get logs count
curl "http://localhost:8030/api/v1/logs/count/total?service_name=notification-service"

# Get service statistics
curl "http://localhost:8030/api/v1/logs/stats/services"
```

### 3. Direct Client Usage
```python
from services.logging_client import logging_client

# Get recent logs
logs = await logging_client.get_logs(limit=10, service_name="notification-service")

# Get specific log
log = await logging_client.get_log_by_id(123)

# Get service stats
stats = await logging_client.get_services_stats()
```

## Logged Data

### Request Information
- Service name: `notification-service`
- HTTP method and path
- Query parameters
- Request headers (sensitive ones redacted)
- Request body (sensitive data redacted)
- Client IP address
- User agent

### Response Information
- Status code
- Response body (sensitive data redacted)
- Processing time in milliseconds

### Enhanced Sensitive Data Filtering

#### Comprehensive Field Detection (40+ patterns):
**Password Related:**
- password, passwd, pwd, pass, passphrase
- confirm_password, new_password, old_password, current_password
- password_confirmation, password_confirm, repeat_password

**Authentication Tokens:**
- token, access_token, refresh_token, auth_token, bearer_token
- jwt, jwt_token, session_token, csrf_token, xsrf_token

**API Keys & Secrets:**
- secret, api_key, apikey, api_secret, client_secret
- private_key, public_key, encryption_key, signing_key

**Authentication:**
- auth, authorization, credential, credentials
- session, session_id, cookie, cookies

**Personal Information:**
- pin, ssn, social_security, social_security_number
- credit_card, card_number, card_num, cvv, cvc, cvv2
- bank_account, account_number, routing_number

**Other Sensitive Data:**
- otp, verification_code, reset_code, activation_code
- security_question, security_answer, backup_codes

#### Smart Value Masking:
- Short values (≤2 chars): `***`
- Medium values (3-6 chars): `a****f` (first + stars + last)
- Long values (>6 chars): `ab****ef` (first 2 + stars + last 2)

#### Text Pattern Masking:
- Form data: `password=secret123` → `password=***`
- Query strings: `token=abc123` → `token=***`
- Credit cards: `4111-1111-1111-1111` → `****-****-****-****`

## Testing

### Basic Integration Test
```bash
python test_logging_integration.py
```

This will:
1. Test connection to the logging service
2. Make sample API requests (generates logs)
3. Query logs via the API endpoints
4. Test direct client access

### Security Features Test
```bash
python test_security_logging.py
```

This comprehensive test verifies:
1. **Sensitive Data Filtering**: Tests masking of passwords, tokens, API keys
2. **Header Filtering**: Tests redaction of authorization headers
3. **Large Body Handling**: Tests body size limits
4. **Excluded Paths**: Tests that health checks aren't logged
5. **Content Type Handling**: Tests different content types (JSON, form data, text)
6. **Log Verification**: Confirms no sensitive data appears in actual logs

## API Documentation

- **Notification Service**: http://localhost:8030/docs
- **Logging Service**: http://0.0.0.0:8020/docs

## Architecture

```
┌─────────────────────┐    ┌─────────────────────┐
│  Notification API   │    │   Logging Service   │
│                     │    │                     │
│  ┌───────────────┐  │    │  ┌───────────────┐  │
│  │   Middleware  │──┼────┼─▶│   Log Storage │  │
│  └───────────────┘  │    │  └───────────────┘  │
│                     │    │                     │
│  ┌───────────────┐  │    │  ┌───────────────┐  │
│  │ Logging Client│──┼────┼─▶│   Query API   │  │
│  └───────────────┘  │    │  └───────────────┘  │
│                     │    │                     │
│  ┌───────────────┐  │    │                     │
│  │   Logs API    │──┼────┼─────────────────────┤
│  └───────────────┘  │    │                     │
└─────────────────────┘    └─────────────────────┘
```

## Benefits

1. **Centralized Logging**: All microservices log to the same service
2. **Automatic Capture**: No manual logging code needed for API requests
3. **Security**: Sensitive data is automatically filtered
4. **Performance Monitoring**: Request processing times are tracked
5. **Debugging**: Easy to trace requests across services
6. **Analytics**: Service usage statistics and patterns
