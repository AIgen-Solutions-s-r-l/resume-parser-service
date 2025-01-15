from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import Settings
from app.core.logging_config import init_logging, test_connection
from app.routers.resume_ingestor_router import router as resume_router
from app.services.resume_service import resume_parser

# Inizializza le impostazioni
settings = Settings()

# Testa la connessione prima
test_connection(settings.syslog_host, settings.syslog_port)

# Inizializza il logger
logger = init_logging(settings)

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield

# Inizializza l'app FastAPI
app = FastAPI(
    title="Resume Ingestor API",
    description="Service per l'ingestione dei resume",
    version="1.0.0",
    lifespan=lifespan
)

# Log dell'avvio dell'applicazione
logger.info(
    "Initializing application",
    extra={
        "event_type": "service_startup",
        "service_name": settings.service_name,
        "environment": settings.environment
    }
)

# Configura il middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=600,
)

@app.get("/")
async def root():
    """Endpoint root che restituisce lo stato del servizio"""
    logger.debug(
        "Root endpoint accessed",
        extra={
            "event_type": "endpoint_access",
            "endpoint": "root",
            "method": "GET"
        }
    )
    return {"message": "ResumeIngestor Service is up and running!"}

# Includi solo il router per l'ingestione dei resume
app.include_router(resume_router)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    logger.error(
        "Request validation error",
        extra={
            "event_type": "validation_error",
            "error_details": exc.errors(),
            "endpoint": request.url.path,
            "method": request.method
        }
    )
    return JSONResponse(
        status_code=422,
        content={
            "error": "ValidationError",
            "message": "Invalid request data",
            "details": exc.errors()
        }
    )


@app.get("/test-log")
async def test_log():
    """Endpoint di test per il logging"""
    logger.info(
        "Test log message",
        extra={
            "test_id": "123",
            "custom_field": "test value",
            "event_type": "test_log"
        }
    )
    return {"status": "Log sent"}
