from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore"
    )

    # Application settings
    app_name: str = Field(default="Notification Service")
    debug: bool = Field(default=False)

    # Gmail SMTP settings
    smtp_server: str = Field(default="smtp.gmail.com")
    smtp_port: int = Field(default=587)
    smtp_username: str
    smtp_password: str
    smtp_use_tls: bool = Field(default=True)
    # smtp_use_ssl: bool = Field(default=False)  # Add SSL option

    # Email settings
    from_email: str
    from_name: str = Field(default="Notification Service")

    # Template settings
    template_dir: str = Field(default="templates")

    # Logging service settings
    # logging_service_url: str = Field(default="http://logger-service:8020")
    logging_service_url: str = Field(default="http://127.0.0.1:8020")
    enable_request_logging: bool = Field(default=True)
    log_request_body: bool = Field(default=True)
    log_response_body: bool = Field(default=True)
    max_log_body_size: int = Field(default=10000)


# Global settings instance
settings = Settings()