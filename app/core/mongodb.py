from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings
from app.core.logging_config import LogConfig

logger = LogConfig.get_logger()

try:
    logger.info("Initializing MongoDB connection", extra={
        "event_type": "mongodb_init",
        "mongodb_uri": settings.mongodb
    })

    client = AsyncIOMotorClient(
        settings.mongodb,
        serverSelectionTimeoutMS=5000
    )

    # Parse database name from connection string, default to 'resumes' if not specified
    database_name = settings.mongodb.split('/')[-1].split('?')[0] or 'resumes'
    database = client[database_name]
    collection_name = database.get_collection("resumes")

    client.admin.command('ping')
    logger.info("MongoDB connection established", extra={
        "event_type": "mongodb_connected",
        "mongodb_uri": settings.mongodb
    })

except Exception as e:
    logger.error("MongoDB connection failed", extra={
        "event_type": "mongodb_error",
        "error_type": type(e).__name__,
        "error_details": str(e)
    })
    raise