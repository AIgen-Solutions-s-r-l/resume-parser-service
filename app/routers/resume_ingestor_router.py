from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, status, Query, Path
from app.core.exceptions import InvalidResumeDataError, ResumeNotFoundError
from app.schemas.resume import AddResume,UpdateResume
from app.core.auth import get_current_user
from app.services.resume_service import (
    get_resume_by_user_id,
    add_resume,
    update_resume,
    generate_resume_json_from_pdf
    
)
from app.core.logging_config import LogConfig
from typing import Any
from fastapi import APIRouter, HTTPException, Depends, status, UploadFile, File
from app.core.auth import get_current_user
from app.core.logging_config import LogConfig
import os
from typing import Any
from fastapi import APIRouter, HTTPException, Depends, status, UploadFile, File
from app.core.auth import get_current_user
from app.core.logging_config import LogConfig
import os
from io import BytesIO
from PyPDF2 import PdfReader, errors

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

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
    
def is_valid_pdf(file_bytes: bytes) -> bool:
    """
    Validate whether the uploaded file is a valid PDF by attempting to read its structure.
    """
    try:
        # Wrap bytes in a BytesIO object for PdfReader
        file_stream = BytesIO(file_bytes)
        reader = PdfReader(file_stream)
        # Attempt to access pages to confirm validity
        _ = reader.pages[0]
        return True
    except (errors.PdfStreamError, IndexError):
        # PdfStreamError for invalid streams, IndexError if no pages are present
        return False
    except Exception:
        # Catch any unexpected errors
        return False

@router.post(
    "/pdf_to_json",
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Resume successfully converted to JSON"},
        400: {"description": "Invalid resume data or PDF processing error"},
        401: {"description": "Not authenticated"},
        500: {"description": "Internal server error"},
    },
)
async def pdf_to_json(
    pdf_file: UploadFile = File(...),
    current_user=Depends(get_current_user),
) -> Any:
    """Convert a PDF resume to JSON using LLMFormat and return the JSON data."""
    try:
        # Validate file size without loading the entire file into memory
        pdf_file.file.seek(0, 2)
        file_size = pdf_file.file.tell()
        pdf_file.file.seek(0)

        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": "File size exceeds the 10 MB limit."},
            )

        # Read the entire file into memory for validation
        pdf_bytes = await pdf_file.read()

        # Validate format using the full file
        if not is_valid_pdf(pdf_bytes):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": "Invalid file format. Only PDFs are allowed."},
            )

        # Generate the JSON resume from the PDF bytes
        resume_json = await generate_resume_json_from_pdf(pdf_bytes)

        if not resume_json:
            logger.error("Failed to generate resume JSON from PDF.", extra={
                "event_type": "resume_generation_error",
                "user_id": current_user,
            })
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": "Failed to generate resume from PDF."},
            )

        return resume_json

    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", extra={
            "event_type": "pdf_to_json_error",
            "user_id": current_user,
            "error_type": type(e).__name__,
            "error_details": str(e),
        })
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "InternalServerError",
                "message": "An error occurred while processing the PDF resume.",
            },
        )