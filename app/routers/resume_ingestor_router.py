from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, status, Query, Path
from app.core.exceptions import InvalidResumeDataError, ResumeNotFoundError
from app.schemas.resume import AddResume,UpdateResume
from app.core.auth import get_current_user
from app.services.resume_service import (
    get_resume_by_user_id,
    add_resume,
    update_resume
)
from app.core.logging_config import LogConfig

logger = LogConfig.get_logger()

router = APIRouter(
    prefix="/resumes",
    tags=["resumes"],
    responses={
        401: {"description": "Not authenticated"},
        403: {"description": "Not authorized"},
        500: {"description": "Internal server error"}
    }
)


@router.post(
    "/create_resume",
    response_model=AddResume,
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"description": "Resume successfully created"},
        400: {"description": "Invalid resume data"},
        404: {"description": "User not found"},
        500: {"description": "Internal server error"}
    }
)
async def create_resume(
        resume_data: AddResume,
        current_user=Depends(get_current_user)
) -> Any:
    """Create a new resume in the MongoDB database."""

    result = await add_resume(resume_data, current_user)
    if "error" in result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": result["error"]}
        )

    return result


@router.get(
    "/get",
    response_model=AddResume,
    responses={
        200: {"description": "Resume successfully retrieved"},
        401: {"description": "Not authenticated"},
        403: {"description": "Not authorized to access this resume"},
        404: {"description": "Resume not found"},
        500: {"description": "Internal server error"}
    }
)
async def get_resume(
        current_user=Depends(get_current_user)
) -> Any:
    """Retrieve a user's resume from MongoDB."""

    try:
        result = await get_resume_by_user_id(current_user)
        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"message": result["error"]}
            )

        logger.info("Resume retrieved", extra={
            "event_type": "resume_retrieved",
            "user_id": current_user,
        })
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Resume retrieval error", extra={
            "event_type": "resume_retrieval_error",
            "user_id": current_user,
            "error_details": str(e)
        })
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "InternalServerError",
                "message": "An error occurred while retrieving the resume"
            }
        )


@router.post(
    "/update",
    response_model=UpdateResume,
    responses={
        200: {"description": "Resume successfully updated"},
        400: {"description": "Invalid resume data"},
        401: {"description": "Not authenticated"},
        403: {"description": "Not authorized to update this resume"},
        404: {"description": "Resume not found"},
        500: {"description": "Internal server error"}
    }
)
async def update_user_resume(
        resume_data: UpdateResume,
        current_user=Depends(get_current_user)
) -> UpdateResume:
    """Update an existing resume."""

    try:
        result = await update_resume(resume_data, current_user)
        return result

    except ResumeNotFoundError as e:
        logger.warning("Resume not found", extra={
            "event_type": "resume_not_found",
            "user_id": current_user.id,
            "error_details": str(e)
        })
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "NotFound", "message": str(e)}
        )
    except InvalidResumeDataError as e:
        logger.warning("Invalid resume data", extra={
            "event_type": "invalid_resume_data",
            "user_id": current_user.id,
            "error_details": str(e)
        })
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "BadRequest", "message": str(e)}
        )
    except HTTPException as e:
        logger.warning("HTTPException occurred", extra={
            "event_type": "http_exception",
            "user_id": current_user.id,
            "status_code": e.status_code,
            "detail": e.detail
        })
        raise
    except Exception as e:
        logger.error("Resume update error", exc_info=True, extra={
            "event_type": "resume_update_error",
            "user_id": current_user.id,
            "error_details": str(e)
        })
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "InternalServerError",
                "message": "An error occurred while updating the resume"
            }
        )
