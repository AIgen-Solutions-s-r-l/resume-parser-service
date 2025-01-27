import os
from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Configuration class for environment variables and service settings.
    """
    # Service settings
    service_name: str = os.getenv("SERVICE_NAME", "authService")
    environment: Literal["development", "staging", "production"] = os.getenv("ENVIRONMENT", "development")
    debug: bool = os.getenv("DEBUG", "True").lower() == "true"

    # Logging settings
    log_level: str = os.getenv("LOG_LEVEL", "DEBUG")
    syslog_host: str = os.getenv("SYSLOG_HOST", "localhost")
    syslog_port: int = int(os.getenv("SYSLOG_PORT", "5141"))
    json_logs: bool = os.getenv("JSON_LOGS", "True").lower() == "true"
    log_retention: str = os.getenv("LOG_RETENTION", "7 days")

    # MongoDB settings
    mongodb_host: str = os.getenv("MONGODB_HOST", "localhost")
    mongodb_port: int = int(os.getenv("MONGODB_PORT", "27017"))
    mongodb_username: str = os.getenv("MONGODB_USERNAME", "appUser")
    mongodb_password: str = os.getenv("MONGODB_PASSWORD", "password123")
    mongodb_database: str = os.getenv("MONGODB_DATABASE", "resumes")
    mongodb_auth_source: str = os.getenv("MONGODB_AUTH_SOURCE", "main_db")

    # Redis settings
    redis_port: int = int(os.getenv("REDIS_PORT", "6379"))

    # RabbitMQ settings
    rabbitmq_url: str = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
    career_docs_queue: str = os.getenv("CAREER_DOCS_QUEUE", "career_docs_queue")
    career_docs_response_queue: str = os.getenv("CAREER_DOCS_RESPONSE_QUEUE", "career_docs_response_queue")
    application_manager_queue: str = os.getenv("APPLICATION_MANAGER_QUEUE", "middleware_notification_queue")

    # Authentication settings
    secret_key: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    algorithm: str = os.getenv("ALGORITHM", "HS256")
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

    openai_api_key: str = os.getenv("OPENAI_API_KEY", "your-openai-api-key-here")
    document_intelligence_api_key: str = os.getenv("DOCUMENT_INTELLIGENCE_API_KEY", "your-document-intelligence-api-key-here")
    document_intelligence_endpoint: str = os.getenv("DOCUMENT_INTELLIGENCE_ENDPOINT", "your-document-intelligence-endpoint-here")

    # Construct MongoDB URI with auth source
    @property
    def mongodb_uri(self) -> str:
        return f"mongodb://{self.mongodb_username}:{self.mongodb_password}@{self.mongodb_host}:{self.mongodb_port}/{self.mongodb_database}?authSource={self.mongodb_auth_source}"

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
