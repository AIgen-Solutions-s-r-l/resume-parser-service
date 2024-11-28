from contextlib import asynccontextmanager
from threading import Thread

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import Settings
from app.core.exceptions import AuthException  # Se `AuthException` è legato solo all'autenticazione, puoi rimuoverlo
from app.core.rabbitmq_client import RabbitMQClient
from app.core.logging_config import init_logging, test_connection
from app.routers.resume_ingestor_router import router as resume_router

# Inizializza le impostazioni
settings = Settings()

# Testa la connessione prima
test_connection(settings.syslog_host, settings.syslog_port)

# Inizializza il logger
logger = init_logging(settings)

def message_callback(ch, method, properties, body):
    """Callback function to process each message from RabbitMQ."""
    logger.info(
        "Received message from RabbitMQ",
        extra={
            "message_body": body.decode(),
            "exchange": method.exchange,
            "routing_key": method.routing_key,
            "event_type": "rabbitmq_message"
        }
    )

# Istanza globale di RabbitMQClient
rabbit_client = RabbitMQClient(
    rabbitmq_url=settings.rabbitmq_url,
    queue="my_queue",
    callback=message_callback
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager per l'applicazione FastAPI."""
    # Avvio
    rabbit_thread = Thread(target=rabbit_client.start)
    rabbit_thread.start()
    logger.info(
        "RabbitMQ client started",
        extra={
            "event_type": "service_startup",
            "component": "rabbitmq",
            "status": "started"
        }
    )

    yield

    # Arresto
    rabbit_client.stop()
    rabbit_thread.join()
    logger.info(
        "RabbitMQ client stopped",
        extra={
            "event_type": "service_shutdown",
            "component": "rabbitmq",
            "status": "stopped"
        }
    )

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
