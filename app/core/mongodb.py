from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from app.core.config import settings
from app.core.logging_config import LogConfig
from urllib.parse import urlparse

logger = LogConfig.get_logger()

def mask_mongodb_uri(uri: str) -> str:
    """Mask sensitive information in MongoDB URI for logging."""
    parsed = urlparse(uri)
    if parsed.password:
        return uri.replace(parsed.password, "****")
    return uri

try:
    masked_uri = mask_mongodb_uri(settings.mongodb)
    logger.info("Initializing MongoDB connection", extra={
        "event_type": "mongodb_init",
        "mongodb_uri": masked_uri
    })

    client = AsyncIOMotorClient(
        settings.mongodb,
        serverSelectionTimeoutMS=5000,
        maxPoolSize=10,
        retryWrites=True,
        w='majority',
        connectTimeoutMS=5000
    )

    # Parse database name from connection string, default to 'resumes' if not specified
    database_name = settings.mongodb_database
    database = client[database_name]
    collection = database.get_collection("resumes")

    # Verify connection is working
    client.admin.command('ping')
    logger.info("MongoDB connection established", extra={
        "event_type": "mongodb_connected",
        "mongodb_uri": masked_uri,
        "database": settings.mongodb_database
    })

except (ConnectionFailure, ServerSelectionTimeoutError) as e:
    logger.error("MongoDB connection failed", extra={
        "event_type": "mongodb_error",
        "error_type": type(e).__name__,
        "error_details": str(e)
    })
    if 'client' in locals():
        client.close()
    raise

except Exception as e:
    logger.error("Unexpected error during MongoDB initialization", extra={
        "event_type": "mongodb_error",
        "error_type": type(e).__name__,
        "error_details": str(e)
    })
    if 'client' in locals():
        client.close()
    raise