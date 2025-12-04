# app/core/logging_config.py
"""
Logging configuration module.

Provides structured logging with optional Logstash integration for
centralized log management in production environments.
"""
import sys
import socket
import json
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from loguru import logger


class TcpSink:
    """
    TCP Sink for sending logs to Logstash.

    Formats logs in ECS (Elastic Common Schema) compatible JSON format
    and sends them over TCP to a Logstash server.
    """

    def __init__(self, host: str, port: int, app_name: str, environment: str = "development"):
        """
        Initialize TCP sink.

        Args:
            host: Logstash host
            port: Logstash TCP port
            app_name: Application name for service identification
            environment: Deployment environment (development, staging, production)
        """
        self.host = host
        self.port = port
        self.app_name = app_name
        self.environment = environment
        self._socket: Optional[socket.socket] = None

    def _format_timestamp(self, dt: datetime) -> str:
        """Format datetime to ISO8601 with milliseconds."""
        return dt.astimezone(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'

    def _create_log_data(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create ECS-compatible log data structure.

        Args:
            record: Loguru record dictionary

        Returns:
            Formatted log data dict
        """
        timestamp = self._format_timestamp(datetime.now(timezone.utc))

        log_data = {
            "@timestamp": timestamp,
            "message": record["message"],
            "log": {
                "level": record["level"].name.lower(),
                "logger": record["module"],
                "origin": {
                    "function": record["function"],
                    "file": {
                        "line": record["line"],
                        "name": record["file"].name
                    }
                }
            },
            "service": {
                "name": self.app_name,
                "type": "resume-parser"
            },
            "event": {
                "kind": "event",
                "created": timestamp
            },
            "process": {
                "pid": record["process"].id,
                "thread": {
                    "id": record["thread"].id
                }
            },
            "labels": {
                "environment": self.environment
            }
        }

        # Add extra fields (event_type, user_id, etc.)
        if record.get("extra"):
            extra = record["extra"]

            # Extract event_type to top level for easier querying
            if "event_type" in extra:
                log_data["event"]["action"] = extra["event_type"]

            # Add all extra fields
            log_data["labels"]["extra"] = extra

        # Add exception info if present
        if record.get("exception") is not None:
            exc = record["exception"]
            log_data["error"] = {
                "message": str(exc),
                "type": exc.__class__.__name__ if hasattr(exc, '__class__') else "Exception",
            }
            if hasattr(exc, 'traceback'):
                log_data["error"]["stack_trace"] = str(exc.traceback)

        return log_data

    def __call__(self, message) -> None:
        """
        Send log message to Logstash.

        Args:
            message: Loguru message object
        """
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5.0)  # 5 second timeout
            sock.connect((self.host, self.port))

            log_data = self._create_log_data(message.record)
            sock.sendall(json.dumps(log_data).encode() + b'\n')
            sock.close()
        except socket.timeout:
            print(f"Timeout connecting to Logstash at {self.host}:{self.port}", file=sys.stderr)
        except ConnectionRefusedError:
            # Silently ignore if Logstash is not available
            pass
        except Exception as e:
            print(f"Error sending log to Logstash: {e}", file=sys.stderr)


def init_logging(settings) -> logger:
    """
    Initialize logging with application settings.

    Args:
        settings: Application settings object

    Returns:
        Configured logger instance
    """
    try:
        LogConfig.setup_logging(
            app_name=settings.service_name,
            log_level=settings.log_level,
            enable_logstash=getattr(settings, 'enable_logstash', False),
            syslog_host=getattr(settings, 'syslog_host', 'localhost'),
            syslog_port=getattr(settings, 'syslog_port', 5141),
            environment=getattr(settings, 'environment', 'development'),
            json_logs=getattr(settings, 'json_logs', False),
        )
        return logger
    except Exception as e:
        print(f"Failed to initialize logging: {e}", file=sys.stderr)
        # Fallback to basic console logging
        logger.remove()
        logger.add(
            sys.stdout,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}",
            level="INFO",
        )
        return logger


def test_connection(host: str = "localhost", port: int = 5141) -> bool:
    """
    Test connection to Logstash server.

    Args:
        host: Logstash host
        port: Logstash TCP port

    Returns:
        True if connection successful
    """
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5.0)
        sock.connect((host, port))

        timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
        test_msg = {
            "@timestamp": timestamp,
            "message": "Connection test from resume-parser-service",
            "log": {"level": "info"},
            "service": {"name": "connection-test"},
            "event": {"action": "connection_test"},
        }

        sock.send(json.dumps(test_msg).encode() + b'\n')
        sock.close()
        print(f"Logstash connection test successful ({host}:{port})")
        return True
    except socket.timeout:
        print(f"Logstash connection test failed: timeout ({host}:{port})")
        return False
    except ConnectionRefusedError:
        print(f"Logstash connection test failed: connection refused ({host}:{port})")
        return False
    except Exception as e:
        print(f"Logstash connection test failed: {e}")
        return False


class LogConfig:
    """
    Logging configuration manager.

    Provides centralized logging setup with support for:
    - Console output with color formatting
    - Optional JSON format for structured logging
    - Optional Logstash integration via TCP
    """

    _initialized: bool = False

    @classmethod
    def setup_logging(
        cls,
        app_name: str = "resume-parser-service",
        log_level: str = "INFO",
        enable_logstash: bool = False,
        syslog_host: str = "localhost",
        syslog_port: int = 5141,
        environment: str = "development",
        json_logs: bool = False,
    ) -> None:
        """
        Configure loguru logger.

        Args:
            app_name: Application name for log identification
            log_level: Minimum log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            enable_logstash: Whether to enable Logstash TCP sink
            syslog_host: Logstash host
            syslog_port: Logstash TCP port
            environment: Deployment environment
            json_logs: Whether to output JSON format to console
        """
        if cls._initialized:
            return

        # Remove default handler
        logger.remove()

        # Console handler
        if json_logs:
            # JSON format for production/container environments
            logger.add(
                sys.stdout,
                format="{message}",
                level=log_level,
                serialize=True,
            )
        else:
            # Pretty format for development
            logger.add(
                sys.stdout,
                format=(
                    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
                    "<level>{level: <8}</level> | "
                    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
                    "<level>{message}</level>"
                ),
                level=log_level,
                colorize=True,
            )

        # Optional Logstash TCP handler
        if enable_logstash:
            tcp_sink = TcpSink(
                host=syslog_host,
                port=syslog_port,
                app_name=app_name,
                environment=environment,
            )

            logger.add(
                tcp_sink,
                level=log_level,
                enqueue=True,  # Thread-safe async logging
                backtrace=True,
                diagnose=True,
                catch=True,  # Don't crash on logging errors
            )

            logger.info(
                f"Logstash logging enabled",
                extra={
                    "event_type": "logging_configured",
                    "logstash_host": syslog_host,
                    "logstash_port": syslog_port,
                },
            )

        cls._initialized = True

    @staticmethod
    def get_logger():
        """
        Get the configured logger instance.

        Returns:
            Loguru logger
        """
        return logger

    @classmethod
    def reset(cls) -> None:
        """Reset logging configuration (useful for testing)."""
        logger.remove()
        cls._initialized = False


__all__ = ['init_logging', 'test_connection', 'logger', 'LogConfig']