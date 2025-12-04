from typing import Dict, Any, Optional

from pymongo import ReturnDocument
from pymongo.errors import PyMongoError, ConnectionFailure, OperationFailure

from app.core.cache import cache_key, get_cache
from app.core.exceptions import (
    ResumeNotFoundError,
    DatabaseOperationError,
)
from app.core.logging_config import LogConfig
from app.core.mongodb import collection_name
from app.schemas.resume import ResumeBase
from app.services.resume_parser import ResumeParser

logger = LogConfig.get_logger()

resume_parser = ResumeParser()

# Cache TTL constants (in seconds)
RESUME_CACHE_TTL = 300  # 5 minutes
RESUME_EXISTS_CACHE_TTL = 60  # 1 minute


async def get_resume_by_user_id(user_id: int, version: Optional[str] = None) -> Dict[str, Any]:
    """
    Retrieve a resume by user ID with caching.

    Args:
        user_id: The user's ID
        version: Optional version filter

    Returns:
        Resume document as dictionary

    Raises:
        ResumeNotFoundError: If resume doesn't exist
        DatabaseOperationError: If database operation fails
    """
    # Generate cache key
    key = cache_key(user_id, version or "", prefix="resume")
    cache = get_cache()

    # Try cache first
    cached_resume = await cache.get(key)
    if cached_resume is not None:
        logger.debug(
            "Resume retrieved from cache",
            extra={"event_type": "cache_hit", "user_id": user_id},
        )
        return cached_resume

    query = {"user_id": user_id}
    if version:
        query["version"] = version

    try:
        resume = await collection_name.find_one(query)
    except ConnectionFailure as e:
        logger.error(
            "Database connection failed",
            extra={
                "event_type": "database_connection_error",
                "user_id": user_id,
                "error": str(e),
            },
        )
        raise DatabaseOperationError("Database connection failed")
    except OperationFailure as e:
        logger.error(
            "Database operation failed",
            extra={
                "event_type": "database_operation_error",
                "user_id": user_id,
                "error": str(e),
            },
        )
        raise DatabaseOperationError(f"Database query failed: {e}")

    if not resume:
        logger.warning(
            "Resume not found",
            extra={
                "event_type": "resume_not_found",
                "user_id": user_id,
                "version": version,
            },
        )
        return {"error": f"Resume not found for user ID: {user_id}"}

    resume["_id"] = str(resume["_id"])

    # Cache the result
    await cache.set(key, resume, RESUME_CACHE_TTL)

    logger.info(
        "Resume retrieved",
        extra={
            "event_type": "resume_retrieved",
            "user_id": user_id,
            "version": version,
        },
    )
    return resume

async def add_resume(resume: ResumeBase, current_user: int) -> Dict[str, Any]:
    """
    Add a new resume for the user. If an existing resume is found, delete it
    before inserting the new one.

    Args:
        resume: The resume data to insert (without user_id).
        current_user: The ID of the current user.

    Returns:
        The inserted resume document or an error message.

    Raises:
        DatabaseOperationError: If database operation fails
    """
    cache = get_cache()

    try:
        # Check for an existing resume for this user
        existing_resume = await collection_name.find_one({"user_id": current_user})
        if existing_resume:
            logger.warning(
                "Existing resume found, deleting before creating a new one",
                extra={"event_type": "resume_replace", "user_id": current_user},
            )
            delete_result = await collection_name.delete_one({"user_id": current_user})
            if delete_result.deleted_count == 0:
                raise DatabaseOperationError(
                    "Failed to delete existing resume during replacement"
                )

        # Convert the Pydantic model to a dictionary
        resume_dict = resume.model_dump()
        resume_dict["user_id"] = current_user

        # Insert the new resume data
        result = await collection_name.insert_one(resume_dict)
        if result.inserted_id:
            inserted_resume = await collection_name.find_one({"_id": result.inserted_id})
            if inserted_resume:
                inserted_resume["_id"] = str(inserted_resume["_id"])

                # Invalidate cache for this user
                await cache.invalidate_pattern(cache_key(current_user, "", prefix="resume")[:16])

                logger.info(
                    "Resume created successfully",
                    extra={"event_type": "resume_created", "user_id": current_user},
                )
                return inserted_resume

        raise DatabaseOperationError("Failed to insert new resume")

    except (ConnectionFailure, OperationFailure) as e:
        logger.error(
            "Database error during resume creation",
            exc_info=True,
            extra={
                "event_type": "database_error",
                "user_id": current_user,
                "error": str(e),
            },
        )
        raise DatabaseOperationError(f"Database operation failed: {e}")
    except DatabaseOperationError:
        raise
    except PyMongoError as e:
        logger.error(
            "MongoDB error during resume creation",
            exc_info=True,
            extra={
                "event_type": "mongodb_error",
                "user_id": current_user,
                "error": str(e),
            },
        )
        return {"error": "DatabaseError", "message": str(e)}

async def update_resume(resume: ResumeBase, user_id: int) -> Dict[str, Any]:
    """
    Update an existing resume.

    Args:
        resume: The updated resume data
        user_id: The user's ID

    Returns:
        Updated resume document

    Raises:
        ResumeNotFoundError: If resume doesn't exist
        DatabaseOperationError: If database operation fails
    """
    cache = get_cache()

    try:
        existing_resume = await collection_name.find_one({"user_id": user_id})
    except (ConnectionFailure, OperationFailure) as e:
        logger.error(
            "Database error during resume lookup",
            extra={"event_type": "database_error", "user_id": user_id, "error": str(e)},
        )
        raise DatabaseOperationError(f"Database query failed: {e}")

    if not existing_resume:
        logger.warning(
            "Resume not found for update",
            extra={"event_type": "resume_not_found", "user_id": user_id},
        )
        return {"error": f"Resume not found for user ID: {user_id}"}

    resume_data = resume.model_dump()

    # Perform a diff to identify changes (Exclude the 'vector' key from the comparison)
    update_data = {}
    for key, value in resume_data.items():
        if key != "vector" and value is not None and existing_resume.get(key) != value:
            update_data[key] = value

    if not update_data:
        logger.info(
            "No changes detected for update",
            extra={"event_type": "no_changes_detected", "user_id": user_id},
        )
        return {"message": "No changes detected"}

    try:
        updated_resume = await collection_name.find_one_and_update(
            {"user_id": user_id},
            {"$set": resume_data},
            return_document=ReturnDocument.AFTER,
        )
    except (ConnectionFailure, OperationFailure) as e:
        logger.error(
            "Database error during resume update",
            extra={"event_type": "database_error", "user_id": user_id, "error": str(e)},
        )
        raise DatabaseOperationError(f"Database update failed: {e}")

    if updated_resume:
        updated_resume["_id"] = str(updated_resume["_id"])

        # Invalidate cache for this user
        await cache.invalidate_pattern(cache_key(user_id, "", prefix="resume")[:16])

        logger.info(
            "Resume updated",
            extra={"event_type": "resume_updated", "user_id": user_id},
        )
        return updated_resume

    logger.error(
        "Failed to retrieve updated resume",
        extra={"event_type": "resume_update_error", "user_id": user_id},
    )
    return {"error": "Failed to retrieve updated resume"}


async def delete_resume(user_id: int) -> Dict[str, Any]:
    """
    Delete a user's resume.

    Args:
        user_id: The user's ID

    Returns:
        Success message or error

    Raises:
        DatabaseOperationError: If database operation fails
    """
    cache = get_cache()

    try:
        existing_resume = await collection_name.find_one({"user_id": user_id})
        if not existing_resume:
            logger.warning(
                "Resume not found for deletion",
                extra={"event_type": "resume_not_found", "user_id": user_id},
            )
            return {"error": f"Resume not found for user ID: {user_id}"}

        result = await collection_name.delete_one({"user_id": user_id})
        if result.deleted_count > 0:
            # Invalidate cache for this user
            await cache.invalidate_pattern(cache_key(user_id, "", prefix="resume")[:16])

            logger.info(
                "Resume deleted",
                extra={"event_type": "resume_deleted", "user_id": user_id},
            )
            return {"message": f"Resume for user ID {user_id} deleted successfully."}

        logger.error(
            "Resume deletion failed",
            extra={"event_type": "resume_deletion_error", "user_id": user_id},
        )
        return {"error": f"Failed to delete resume for user ID: {user_id}"}

    except (ConnectionFailure, OperationFailure) as e:
        logger.error(
            "Database error during resume deletion",
            extra={"event_type": "database_error", "user_id": user_id, "error": str(e)},
        )
        raise DatabaseOperationError(f"Database operation failed: {e}")
    
async def generate_resume_json_from_pdf(pdf_bytes: bytes) -> str:
    """
    Generate JSON resume from PDF bytes.

    Args:
        pdf_bytes: The PDF file content as bytes

    Returns:
        JSON string of the parsed resume
    """
    resume_data = await resume_parser.generate_resume_from_pdf_bytes(pdf_bytes)
    return resume_data


async def user_has_resume(user_id: int) -> bool:
    """
    Check if the user has a resume in the database with caching.

    Args:
        user_id: The ID of the user.

    Returns:
        True if a resume exists for the user, False otherwise.

    Raises:
        DatabaseOperationError: If database operation fails
    """
    # Generate cache key for exists check
    key = cache_key(user_id, prefix="resume_exists")
    cache = get_cache()

    # Try cache first
    cached_result = await cache.get(key)
    if cached_result is not None:
        return cached_result

    try:
        resume = await collection_name.find_one(
            {"user_id": user_id}, projection={"_id": 1}
        )
        exists = resume is not None

        # Cache the result with shorter TTL
        await cache.set(key, exists, RESUME_EXISTS_CACHE_TTL)

        return exists
    except (ConnectionFailure, OperationFailure) as e:
        logger.error(
            "Database error while checking resume existence",
            extra={
                "event_type": "database_error",
                "user_id": user_id,
                "error": str(e),
            },
        )
        raise DatabaseOperationError(f"Database query failed: {e}")
