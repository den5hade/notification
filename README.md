# Notification Microservice

A FastAPI-based microservice for sending email notifications using Gmail SMTP. This service handles email verification, password change, and support ticket notifications for other microservices.

## Features

- 📧 Email notifications via Gmail SMTP
- 🎨 HTML email templates with responsive design
- 🔒 Support for email verification and password change notifications
- 🎫 **Support Ticket System**: Dual email notifications (user confirmation + support team notification)
- 📝 Pydantic schemas for request/response validation
- 🚀 FastAPI with automatic API documentation
- 🔧 Environment-based configuration
- 📊 Health check endpoints
- 📋 **Logging Integration**: Automatic request/response logging to logging microservice
- 🔍 **Log Query API**: Query and analyze logs via REST endpoints

## Project Structure

```
notification/
├── api/
│   └── api_v1/
│       ├── handlers/
│       │   ├── notification.py        # General notification endpoints
│       │   └── support_ticket.py      # Support ticket endpoints
│       └── routers.py                 # Route configuration
├── core/
│   └── config.py                      # Application settings
├── schemas/
│   ├── notification.py                # General notification models
│   └── support.py                     # Support ticket models
├── services/
│   └── send_email_service.py          # Email service logic
├── templates/
│   ├── email_verification.html        # Email verification template
│   ├── change_password.html           # Password change template
│   ├── support_ticket.html            # Support team notification template
│   └── support_ticket_confirmation.html # User confirmation template
├── app.py                             # FastAPI application
└── pyproject.toml                     # Dependencies
```

## Setup

### 1. Install Dependencies

```bash
uv install
```

### 2. Configure Environment

Copy the example environment file and configure your Gmail settings:

```bash
cp .env.example .env
```

Edit `.env` with your Gmail credentials:

```env
# Gmail SMTP Configuration
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password  # Use App Password, not regular password
FROM_EMAIL=your-email@gmail.com
FROM_NAME=Your Service Name

# Support Team Configuration
SUPPORT_TEAM_EMAIL=support@yourcompany.com
```

### 3. Gmail App Password Setup

1. Enable 2-Factor Authentication on your Gmail account
2. Go to Google Account settings → Security → App passwords
3. Generate an app password for "Mail"
4. Use this app password in the `SMTP_PASSWORD` field

### 4. Run the Service

```bash
# Development mode
uvicorn app:app --reload --host 0.0.0.0 --port 8030

# Or using Python
python app.py
```

## Logging Integration

The notification service is integrated with a logging microservice for automatic request/response logging and log analysis.

### Configuration

Add these settings to your `.env` file:

```env
# Logging Service Settings
LOGGING_SERVICE_URL=http://0.0.0.0:8020
ENABLE_REQUEST_LOGGING=true
```

### Logging Features

- **Automatic Logging**: All API requests/responses are automatically logged
- **Sensitive Data Filtering**: Passwords, tokens, and secrets are redacted
- **Performance Tracking**: Request processing times are recorded
- **Log Query API**: Query logs via REST endpoints

### Logging API Endpoints

- `GET /api/v1/logs/` - Query logs with filtering and pagination
- `GET /api/v1/logs/{log_id}` - Get specific log entry
- `GET /api/v1/logs/count/total` - Get total logs count
- `GET /api/v1/logs/stats/services` - Get service statistics
- `DELETE /api/v1/logs/cleanup` - Cleanup old logs

For detailed logging integration documentation, see [LOGGING_INTEGRATION.md](LOGGING_INTEGRATION.md).

## API Usage

### Send Notification

**POST** `/api/v1/notifications/send`

#### Email Verification Request:
```json
{
  "email": "user@example.com",
  "task": "email_verification",
  "link": "http://localhost:8000/api/v1/auth/verify-email?token=8d9a1b50-e4f1-47b2-bd3b-37245db5c9db",
  "user_name": "User Name",
  "subject": "Please verify your email address"
}
```

#### Password Change Request:
```json
{
  "email": "user@example.com",
  "task": "change_password",
  "link": "http://localhost:8000/api/v1/auth/change-password?token=...",
  "user_name": "User Name",
  "subject": "Password Change Request"
}
```

#### Response:
```json
{
  "success": true,
  "message": "Email sent successfully",
  "email": "user@example.com",
  "task": "email_verification"
}
```

### Send Support Ticket Notification

**POST** `/api/v1/support-ticket`

Sends dual email notifications: one confirmation to the user and one notification to the support team.

#### Support Ticket Request:
```json
{
  "email": "support@yourcompany.com",
  "task": "support_ticket",
  "link": "https://portal.yourcompany.com/ticket/12345",
  "user_name": "Support Team",
  "subject": "New Support Ticket Created - TICKET-12345",
  "user_email": "requester@example.com",
  "category": "login",
  "ticket_id": "TICKET-12345",
  "priority": "High",
  "description": "User unable to log in after password reset. Error: Invalid credentials",
  "due_date": "2024-01-15T18:00:00Z"
}
```

#### Support Ticket Request (Minimal):
```json
{
  "email": "support@yourcompany.com",
  "task": "support_ticket",
  "link": "https://portal.yourcompany.com/ticket/12345",
  "user_name": "Support Team",
  "subject": "New Support Ticket Created",
  "user_email": "requester@example.com",
  "category": "product_service",
  "ticket_id": "TICKET-12345",
  "priority": "Medium",
  "description": "Product search is not returning expected results"
}
```

#### Support Ticket Response:
```json
{
  "success": true,
  "message": "Support ticket processed successfully - confirmation sent to user and notification sent to support team",
  "ticket_id": "TICKET-12345",
  "user_email_result": {
    "success": true,
    "message": "Confirmation email sent to user",
    "email": "requester@example.com"
  },
  "support_email_result": {
    "success": true,
    "message": "Notification email sent to support team",
    "email": "support@yourcompany.com"
  }
}
```

#### Support Ticket Response (Partial Failure):
```json
{
  "success": false,
  "message": "Failed to send: user confirmation email",
  "ticket_id": "TICKET-12345",
  "user_email_result": {
    "success": false,
    "message": "Failed to send confirmation email: SMTP connection error",
    "email": "requester@example.com"
  },
  "support_email_result": {
    "success": true,
    "message": "Notification email sent to support team",
    "email": "support@yourcompany.com"
  }
}
```

### Health Check

**GET** `/health` or `/api/v1/notifications/health`

```json
{
  "status": "healthy",
  "service": "Notification Service"
}
```

## API Documentation

Once the service is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Email Templates

The service includes responsive HTML templates for:

1. **Email Verification** (`templates/email_verification.html`)
   - Clean, professional design
   - Clear call-to-action button
   - Security warnings and expiration notice

2. **Password Change** (`templates/change_password.html`)
   - Security-focused design
   - Warning for unauthorized requests
   - Time-sensitive action notice

3. **Support Ticket Notification** (`templates/support_ticket.html`)
   - Professional support team notification
   - Complete ticket details with priority indicators
   - Requester information and issue description
   - Action-oriented design for support staff

4. **Support Ticket Confirmation** (`templates/support_ticket_confirmation.html`)
   - User-friendly confirmation message
   - Ticket details and next steps
   - Clear expectations and timeline
   - Professional confirmation design

## Support Ticket Categories and Priorities

### Categories
- `login` - Login and authentication issues
- `product_service` - Product or service-related problems
- `search` - Search functionality issues
- `store_service` - Store or e-commerce related issues
- `other` - Other miscellaneous issues

### Priorities
- `High` - Critical issues requiring immediate attention
- `Medium` - Important issues with standard response time
- `Low` - Minor issues or feature requests

## Development

### Adding New Notification Types

1. Add new task type to `NotificationTask` enum in `schemas/notification.py`
2. Create new HTML template in `templates/`
3. Update template mapping in `services/send_email_service.py`

### Support Ticket Workflow

The support ticket system automatically sends two emails:

1. **User Confirmation Email**: Sent to the `user_email` address with ticket details and next steps
2. **Support Team Notification**: Sent to the configured `SUPPORT_TEAM_EMAIL` with complete ticket information

Both emails use separate templates and provide different information appropriate for each recipient.

### Testing

```bash
# Install test dependencies
uv add pytest pytest-asyncio httpx

# Run tests
pytest
```

## Production Deployment

1. Set `DEBUG=false` in environment
2. Configure proper CORS origins
3. Use environment variables for sensitive data
4. Consider using a proper SMTP service for production
5. Set up proper logging and monitoring

## Security Notes

- Never commit `.env` file to version control
- Use Gmail App Passwords, not regular passwords
- Configure CORS properly for production
- Consider rate limiting for production use
- Validate and sanitize all input data