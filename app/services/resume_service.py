from typing import Dict, Any, Optional
from app.schemas.resume import Resume
from pymongo.errors import DuplicateKeyError
from app.core.mongodb import collection_name
from app.core.logging_config import LogConfig
from pymongo import ReturnDocument

logger = LogConfig.get_logger()

async def get_resume_by_user_id(user_id: int, version: Optional[str] = None) -> Dict[str, Any]:
    try:
        # Ensure user_id is an integer
        if not isinstance(user_id, int):
            try:
                user_id = int(user_id)
            except ValueError:
                logger.error("Invalid user ID format", extra={
                    "event_type": "resume_validation_error",
                    "user_id": user_id
                })
                return {"error": f"Invalid user ID format: {user_id}. Must be an integer."}

        # Build the query
        query = {"user_id": user_id}
        if version:
            query["version"] = version

        # Check if the resume exists
        resume = await collection_name.find_one(query)
        if not resume:
            logger.warning("Resume not found", extra={
                "event_type": "resume_not_found",
                "user_id": user_id,
                "version": version
            })
            return {"error": f"Resume not found for user ID: {user_id}"}

        # Convert ObjectId to string
        resume["_id"] = str(resume["_id"])

        logger.info("Resume retrieved", extra={
            "event_type": "resume_retrieved",
            "user_id": user_id,
            "version": version
        })
        return resume

    except Exception as e:
        logger.error(f"Error retrieving resume: {str(e)}", extra={
            "event_type": "resume_retrieval_error",
            "user_id": user_id,
            "version": version,
            "error_type": type(e).__name__,
            "error_details": str(e)
        })
        return {"error": f"Error retrieving resume: {str(e)}"}


async def add_resume(resume: Resume, current_user: int) -> Dict[str, Any]:
    try:
        # Ensure current_user is an integer
        if not isinstance(current_user, int):
            try:
                current_user = int(current_user)
            except ValueError:
                logger.error("Invalid user ID format", extra={
                    "event_type": "resume_validation_error",
                    "user_id": current_user
                })
                return {"error": f"Invalid user ID format: {current_user}. Must be an integer."}

        # Check if a resume already exists for the provided user_id
        existing_resume = await collection_name.find_one({"user_id": current_user})
        if existing_resume:
            logger.warning("Resume already exists", extra={
                "event_type": "resume_duplicate",
                "user_id": current_user
            })
            return {"error": f"Resume already exists for user ID: {current_user}"}

        # Explicitly add the user_id field to the resume document
        resume.user_id = current_user

        # Insert the document into the database
        result = await collection_name.insert_one(resume.model_dump())
        if result.inserted_id:
            inserted_resume = await collection_name.find_one({"_id": result.inserted_id})
            if inserted_resume:
                # Convert the ObjectId to string for the client
                inserted_resume["_id"] = str(inserted_resume["_id"])
                logger.info("Resume created", extra={
                    "event_type": "resume_created",
                    "user_id": current_user
                })
                return inserted_resume

        logger.error("Resume insertion failed", extra={
            "event_type": "resume_creation_error",
            "user_id": current_user
        })
        return {"error": "Failed to retrieve inserted resume"}
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", extra={
            "event_type": "resume_creation_error",
            "user_id": current_user,
            "error_type": type(e).__name__,
            "error_details": str(e)
        })
        return {"error": f"Unexpected error: {str(e)}"}


async def update_resume(resume: Resume, current_user: int) -> Dict[str, Any]:
    try:
        # Ensure current_user is an integer
        if not isinstance(current_user, int):
            try:
                current_user = int(current_user)
            except ValueError:
                logger.error("Invalid user ID format", extra={
                    "event_type": "resume_validation_error",
                    "user_id": current_user
                })
                return {"error": f"Invalid user ID format: {current_user}. Must be an integer."}

        # Check if the resume exists
        existing_resume = await collection_name.find_one({"user_id": current_user})
        if not existing_resume:
            logger.warning("Resume not found for update", extra={
                "event_type": "resume_not_found",
                "user_id": current_user
            })
            return {"error": f"Resume not found for user ID: {current_user}"}

        # Update the resume
        resume_data = resume.model_dump()
        resume_data["user_id"] = current_user  # Ensure user_id is correct

        updated_resume = await collection_name.find_one_and_update(
            {"user_id": current_user},
            {"$set": resume_data},
            return_document=ReturnDocument.AFTER
        )

        if updated_resume:
            updated_resume["_id"] = str(updated_resume["_id"])
            logger.info("Resume updated", extra={
                "event_type": "resume_updated",
                "user_id": current_user
            })
            return updated_resume
        else:
            logger.error("Failed to retrieve updated resume", extra={
                "event_type": "resume_update_error",
                "user_id": current_user
            })
            return {"error": "Failed to retrieve updated resume"}

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", extra={
            "event_type": "resume_update_error",
            "user_id": current_user,
            "error_type": type(e).__name__,
            "error_details": str(e)
        })
        return {"error": f"Unexpected error: {str(e)}"}


async def delete_resume(current_user: int) -> Dict[str, Any]:
    try:
        # Ensure current_user is an integer
        if not isinstance(current_user, int):
            try:
                current_user = int(current_user)
            except ValueError:
                logger.error("Invalid user ID format", extra={
                    "event_type": "resume_validation_error",
                    "user_id": current_user
                })
                return {"error": f"Invalid user ID format: {current_user}. Must be an integer."}

        # Check if the resume exists
        existing_resume = await collection_name.find_one({"user_id": current_user})
        if not existing_resume:
            logger.warning("Resume not found for deletion", extra={
                "event_type": "resume_not_found",
                "user_id": current_user
            })
            return {"error": f"Resume not found for user ID: {current_user}"}

        # Delete the resume
        result = await collection_name.delete_one({"user_id": current_user})
        if result.deleted_count > 0:
            logger.info("Resume deleted", extra={
                "event_type": "resume_deleted",
                "user_id": current_user
            })
            return {"message": f"Resume for user ID {current_user} deleted successfully."}
        else:
            logger.error("Resume deletion failed", extra={
                "event_type": "resume_deletion_error",
                "user_id": current_user
            })
            return {"error": f"Failed to delete resume for user ID: {current_user}"}

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", extra={
            "event_type": "resume_deletion_error",
            "user_id": current_user,
            "error_type": type(e).__name__,
            "error_details": str(e)
        })
        return {"error": f"Unexpected error: {str(e)}"}


async def list_resumes(skip: int = 0, limit: int = 10) -> Dict[str, Any]:
    try:
        # Fetch total count of resumes
        total_count = await collection_name.count_documents({})

        # Fetch resumes with pagination
        cursor = collection_name.find({}).skip(skip).limit(limit)
        resumes = []
        async for resume in cursor:
            resume["_id"] = str(resume["_id"])
            resumes.append(resume)

        logger.info("Resumes listed", extra={
            "event_type": "resumes_listed",
            "skip": skip,
            "limit": limit
        })
        return {
            "total": total_count,
            "resumes": resumes,
            "skip": skip,
            "limit": limit
        }

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", extra={
            "event_type": "resume_list_error",
            "error_type": type(e).__name__,
            "error_details": str(e),
            "skip": skip,
            "limit": limit
        })
        return {"error": f"Unexpected error: {str(e)}"}


async def search_resumes(query: Dict[str, Any], skip: int = 0, limit: int = 10) -> Dict[str, Any]:
    try:
        # Fetch total count of resumes matching the query
        total_count = await collection_name.count_documents(query)

        # Fetch resumes with pagination
        cursor = collection_name.find(query).skip(skip).limit(limit)
        resumes = []
        async for resume in cursor:
            resume["_id"] = str(resume["_id"])
            resumes.append(resume)

        logger.info("Resumes searched", extra={
            "event_type": "resumes_searched",
            "query": query,
            "skip": skip,
            "limit": limit
        })
        return {
            "total": total_count,
            "resumes": resumes,
            "skip": skip,
            "limit": limit
        }

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", extra={
            "event_type": "resume_search_error",
            "error_type": type(e).__name__,
            "error_details": str(e),
            "query": query,
            "skip": skip,
            "limit": limit
        })
        return {"error": f"Unexpected error: {str(e)}"}
