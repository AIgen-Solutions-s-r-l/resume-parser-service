# app/main.py
"""
FastAPI application entry point.
"""
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from app.core.cache import get_cache
from app.core.config import settings
from app.core.dependencies import DatabaseManager
from app.core.indexes import ensure_indexes
from app.core.logging_config import init_logging, test_connection
from app.core.middleware import RequestLoggingMiddleware, setup_exception_handlers
from app.routers.healthcheck_router import router as healthcheck_router
from app.routers.resume_ingestor_router import router as resume_router
from app.services.resume_service import resume_parser

# Validate production settings at startup
settings.validate_production_settings()

# Test logstash connection if enabled
if settings.enable_logstash:
    test_connection(settings.syslog_host, settings.syslog_port)

# Initialize logger
logger = init_logging(settings)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.

    Handles startup and shutdown events:
    - Startup: Initialize database connection, indexes, cache, and thread pool
    - Shutdown: Close connections and cleanup resources
    """
    # Startup
    logger.info(
        "Starting application",
        extra={
            "event_type": "service_startup",
            "service_name": settings.service_name,
            "environment": settings.environment,
        },
    )

    # Initialize thread pool executor
    app.state.executor = ThreadPoolExecutor(max_workers=10)
    resume_parser.set_executor(app.state.executor)

    # Initialize database connection
    db_manager = DatabaseManager.get_instance()
    try:
        await db_manager.connect()
        app.state.db_manager = db_manager

        # Create database indexes for query optimization
        index_results = await ensure_indexes(db_manager.database)
        logger.info(
            "Database indexes initialized",
            extra={"event_type": "indexes_initialized", "results": index_results},
        )
    except ConnectionError as e:
        logger.error(
            "Failed to connect to database during startup",
            extra={"event_type": "startup_error", "error": str(e)},
        )
        # Re-raise to prevent app from starting without database
        raise

    # Initialize cache
    cache = get_cache()
    await cache.start()
    app.state.cache = cache

    yield

    # Shutdown
    logger.info("Shutting down application", extra={"event_type": "service_shutdown"})

    # Stop cache cleanup task
    await cache.stop()

    # Close database connection
    await db_manager.disconnect()

    # Shutdown thread pool
    app.state.executor.shutdown(wait=True)


# Initialize FastAPI application
app = FastAPI(
    title="Resume Ingestor API",
    description="Service for resume ingestion and parsing",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=600,
)

# Add GZip compression for responses > 500 bytes
app.add_middleware(GZipMiddleware, minimum_size=500)

# Add request logging middleware
app.add_middleware(RequestLoggingMiddleware)

# Setup exception handlers
setup_exception_handlers(app)

# Include routers
app.include_router(resume_router)
app.include_router(healthcheck_router)


@app.get("/")
async def root():
    """Root endpoint returning service status."""
    return {"message": "ResumeIngestor Service is up and running!"}


@app.get("/test-log")
async def test_log():
    """Test endpoint for logging verification."""
    logger.info(
        "Test log message",
        extra={
            "test_id": "123",
            "custom_field": "test value",
            "event_type": "test_log",
        },
    )
    return {"status": "Log sent"}
