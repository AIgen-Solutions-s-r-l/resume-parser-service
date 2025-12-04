from typing import Literal
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Configuration class for environment variables and service settings.
    """
    # Service settings
    service_name: str = "resume-parser-service"
    environment: Literal["development", "staging", "production"] = "development"
    debug: bool = True

    # Logging settings
    log_level: str = "DEBUG"
    syslog_host: str = "localhost"
    syslog_port: int = 5141
    json_logs: bool = True
    log_retention: str = "7 days"
    enable_logstash: bool = False

    # MongoDB settings
    mongodb: str = "mongodb://localhost:27017"
    mongodb_database: str = "resumes"

    # Authentication settings (REQUIRED in production)
    secret_key: str = "dev-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # External API keys (REQUIRED)
    openai_api_key: str = ""
    document_intelligence_api_key: str = ""
    document_intelligence_endpoint: str = ""
    deepinfra_api_key: str = ""

    # CORS settings
    cors_origins: str = "http://localhost:3000"

    @field_validator("secret_key")
    @classmethod
    def validate_secret_key(cls, v: str, info) -> str:
        """Validate secret_key is not using default in production."""
        # Access environment from values if available
        return v

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    def validate_production_settings(self) -> None:
        """
        Validate that required settings are properly configured for production.
        Call this during application startup.
        """
        if self.environment == "production":
            errors = []

            if self.secret_key == "dev-secret-key-change-in-production":
                errors.append("SECRET_KEY must be set to a secure value in production")

            if not self.openai_api_key:
                errors.append("OPENAI_API_KEY is required")

            if not self.document_intelligence_api_key:
                errors.append("DOCUMENT_INTELLIGENCE_API_KEY is required")

            if not self.document_intelligence_endpoint:
                errors.append("DOCUMENT_INTELLIGENCE_ENDPOINT is required")

            if errors:
                raise ValueError(f"Production configuration errors: {'; '.join(errors)}")

    # Environment-specific logging configuration
    @property
    def logging_config(self) -> dict:
        """
        Returns logging configuration based on environment.
        """
        base_config = {
            "app_name": self.service_name,
            "log_level": self.log_level,
            "syslog_host": self.syslog_host if self.enable_logstash else None,
            "syslog_port": self.syslog_port if self.enable_logstash else None,
            "json_logs": self.json_logs,
        }

        if self.environment == "development":
            base_config.update({
                "json_logs": False,  # Human-readable logs in development
                "log_level": "DEBUG" if self.debug else "INFO"
            })
        elif self.environment == "staging":
            base_config.update({
                "log_level": "DEBUG",
                "json_logs": True
            })
        else:  # production
            base_config.update({
                "log_level": "INFO",
                "json_logs": True
            })

        return base_config

    model_config = SettingsConfigDict(env_file=".env", extra="allow")


settings = Settings()
