from typing import Dict, Any, Optional
from app.schemas.resume import AddResume, UpdateResume
from app.core.mongodb import collection_name
from app.core.logging_config import LogConfig
from pymongo import ReturnDocument
from app.services.resume_parser import ResumeParser

logger = LogConfig.get_logger()

resume_parser = ResumeParser()

async def get_resume_by_user_id(user_id: int, version: Optional[str] = None) -> Dict[str, Any]:
    try:
        query = {"user_id": user_id}
        if version:
            query["version"] = version

        resume = await collection_name.find_one(query)
        if not resume:
            logger.warning("Resume not found", extra={
                "event_type": "resume_not_found",
                "user_id": user_id,
                "version": version
            })
            return {"error": f"Resume not found for user ID: {user_id}"}

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


async def add_resume(resume: AddResume, current_user: int) -> Dict[str, Any]:
    try:
        existing_resume = await collection_name.find_one({"user_id": current_user})
        if existing_resume:
            logger.warning("Resume already exists", extra={
                "event_type": "resume_duplicate",
                "user_id": current_user
            })
            return {"error": f"Resume already exists for user ID: {current_user}"}

        resume.user_id = current_user

        result = await collection_name.insert_one(resume.model_dump())
        if result.inserted_id:
            inserted_resume = await collection_name.find_one({"_id": result.inserted_id})
            if inserted_resume:
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


async def update_resume(resume: UpdateResume, user_id: int) -> Dict[str, Any]:
    try:
        existing_resume = await collection_name.find_one({"user_id": user_id})
        if not existing_resume:
            logger.warning("Resume not found for update", extra={
                "event_type": "resume_not_found",
                "user_id": user_id
            })
            return {"error": f"Resume not found for user ID: {user_id}"}

        resume_data = resume.model_dump()

        # Perform a diff to identify changes (Exclude the 'vector' key from the comparison)
        update_data = {}
        for key, value in resume_data.items():
            if key != "vector" and value is not None and existing_resume.get(key) != value:
                update_data[key] = value

        if not update_data:
            logger.info("No changes detected for update", extra={
                "event_type": "no_changes_detected",
                "user_id": user_id
            })
            return {"message": "No changes detected"}

        updated_resume = await collection_name.find_one_and_update(
            {"user_id": user_id},
            {"$set": resume_data},
            return_document=ReturnDocument.AFTER
        )

        if updated_resume:
            updated_resume["_id"] = str(updated_resume["_id"])
            logger.info("Resume updated", extra={
                "event_type": "resume_updated",
                "user_id": user_id
            })
            return updated_resume
        else:
            logger.error("Failed to retrieve updated resume", extra={
                "event_type": "resume_update_error",
                "user_id": user_id
            })
            return {"error": "Failed to retrieve updated resume"}

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", extra={
            "event_type": "resume_update_error",
            "user_id": user_id,
            "error_type": type(e).__name__,
            "error_details": str(e)
        })
        return {"error": f"Unexpected error: {str(e)}"}


async def delete_resume(user_id: int) -> Dict[str, Any]:
    try:
        existing_resume = await collection_name.find_one({"user_id": user_id})
        if not existing_resume:
            logger.warning("Resume not found for deletion", extra={
                "event_type": "resume_not_found",
                "user_id": user_id
            })
            return {"error": f"Resume not found for user ID: {user_id}"}

        result = await collection_name.delete_one({"user_id": user_id})
        if result.deleted_count > 0:
            logger.info("Resume deleted", extra={
                "event_type": "resume_deleted",
                "user_id": user_id
            })
            return {"message": f"Resume for user ID {user_id} deleted successfully."}
        else:
            logger.error("Resume deletion failed", extra={
                "event_type": "resume_deletion_error",
                "user_id": user_id
            })
            return {"error": f"Failed to delete resume for user ID: {user_id}"}

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", extra={
            "event_type": "resume_deletion_error",
            "user_id": user_id,
            "error_type": type(e).__name__,
            "error_details": str(e)
        })
        return {"error": f"Unexpected error: {str(e)}"}
    
async def generate_resume_json_from_pdf(pdf_bytes: bytes) -> str:
    """Given PDF bytes and OpenAI API key, returns the JSON resume."""
    resume_data = await resume_parser.generate_resume_from_pdf_bytes(pdf_bytes)
    return resume_data
