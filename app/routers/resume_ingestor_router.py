import json
from typing import Any
from fastapi import APIRouter, HTTPException, Depends, status, UploadFile, File
from io import BytesIO
from PyPDF2 import PdfReader, errors
from app.core.auth import get_current_user
from app.core.logging_config import LogConfig
from app.core.exceptions import InvalidResumeDataError, ResumeNotFoundError
from app.schemas.resume import UpdateResume, AddResume, GetResume
from app.services.resume_service import (
    get_resume_by_user_id,
    add_resume,
    update_resume,
    generate_resume_json_from_pdf,
)

# Constants
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

# Logger
logger = LogConfig.get_logger()

# Router
router = APIRouter(
    prefix="/resumes",
    tags=["resumes"],
    responses={
        401: {"description": "Not authenticated"},
        403: {"description": "Not authorized"},
        500: {"description": "Internal server error"},
    },
)

def validate_file_size_and_format(file: UploadFile) -> bytes:
    """
    Validate file size and format. Log details and return file content if valid.

    Args:
        file (UploadFile): Uploaded file to validate.

    Returns:
        bytes: Content of the uploaded file.

    Raises:
        HTTPException: If file size exceeds the limit or format is invalid.
    """
    file.file.seek(0, 2)
    size = file.file.tell()
    file.file.seek(0)

    if size > MAX_FILE_SIZE:
        logger.warning(
            "File too large",
            extra={"event_type": "file_size_error", "file_size": size, "max_size": MAX_FILE_SIZE},
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size exceeds the 10 MB limit.",
        )

    file_bytes = file.file.read()

    try:
        PdfReader(BytesIO(file_bytes)).pages[0]  # Validate PDF
        logger.info("File validated successfully", extra={"event_type": "file_validation"})
    except (errors.PdfStreamError, IndexError):
        logger.warning(
            "Invalid file format",
            extra={"event_type": "file_format_error", "file_name": file.filename},
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file format. Only PDFs are allowed.",
        )

    return file_bytes

@router.post(
    "/create_resume",
    status_code=status.HTTP_201_CREATED,
    response_model=AddResume,
    responses={
        201: {"description": "Resume successfully created"},
        400: {"description": "Invalid resume data"},
        404: {"description": "User not found"},
        500: {"description": "Internal server error"},
    },
)
async def create_resume(resume_data: AddResume, current_user=Depends(get_current_user)) -> Any:
    """Create a new resume in the database."""
    try:
        logger.info(
            "Attempting to add resume to the database",
            extra={"event_type": "database_operation_start", "user_id": current_user},
        )
        result = await add_resume(resume_data, current_user)
        
        if "error" in result:
            logger.error(
                "Error encountered during resume creation",
                extra={
                    "event_type": "resume_creation_error",
                    "user_id": current_user,
                    "error_details": result["error"],
                },
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail={"message": result["error"]}
            )

        logger.info(
            "Resume created successfully",
            extra={
                "event_type": "resume_created",
                "user_id": current_user,
                "resume_id": result.get("resume_id", "unknown"),
            },
        )
        return result
    except Exception as e:
        logger.error(
            "Unexpected error during resume creation",
            exc_info=True,
            extra={
                "event_type": "unexpected_error",
                "user_id": current_user,
                "error_details": str(e),
                "resume_data": resume_data.model_dump(exclude_unset=True) if hasattr(resume_data, "model_dump") else str(resume_data),
            },
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while creating the resume.",
        )

@router.get(
    "/get",
    response_model=GetResume,
    responses={
        200: {"description": "Resume successfully retrieved"},
        401: {"description": "Not authenticated"},
        403: {"description": "Not authorized to access this resume"},
        404: {"description": "Resume not found"},
        500: {"description": "Internal server error"},
    },
)
async def get_resume(current_user=Depends(get_current_user)) -> Any:
    """Retrieve a user's resume from the database."""
    try:
        result = await get_resume_by_user_id(current_user)
        if "error" in result:
            logger.warning(
                "Resume not found",
                extra={"event_type": "resume_not_found", "user_id": current_user},
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail={"message": result["error"]}
            )
        logger.info("Resume retrieved", extra={"event_type": "resume_retrieved", "user_id": current_user})
        return result
    except Exception as e:
        logger.error(
            "Unexpected error during resume retrieval",
            exc_info=True,
            extra={"event_type": "unexpected_error", "user_id": current_user, "error_details": str(e)},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while retrieving the resume.",
        )

@router.put(
    "/update",
    response_model=UpdateResume,
    responses={
        200: {"description": "Resume successfully updated"},
        400: {"description": "Invalid resume data"},
        401: {"description": "Not authenticated"},
        403: {"description": "Not authorized to update this resume"},
        404: {"description": "Resume not found"},
        500: {"description": "Internal server error"},
    },
)
async def update_user_resume(resume_data: UpdateResume, current_user=Depends(get_current_user)) -> UpdateResume:
    """Update an existing resume."""
    try:
        result = await update_resume(resume_data, current_user)
        logger.info("Resume updated", extra={"event_type": "resume_updated", "user_id": current_user})
        return result
    except ResumeNotFoundError as e:
        logger.warning(
            "Resume not found during update",
            extra={"event_type": "resume_not_found", "user_id": current_user, "error_details": str(e)},
        )
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"message": str(e)})
    except InvalidResumeDataError as e:
        logger.warning(
            "Invalid resume data during update",
            extra={"event_type": "invalid_resume_data", "user_id": current_user, "error_details": str(e)},
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"message": str(e)})
    except Exception as e:
        logger.error(
            "Unexpected error during resume update",
            exc_info=True,
            extra={"event_type": "unexpected_error", "user_id": current_user, "error_details": str(e)},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while updating the resume.",
        )

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
async def pdf_to_json(pdf_file: UploadFile = File(...), current_user=Depends(get_current_user)) -> GetResume:
    """Convert a PDF resume to JSON."""
    try:
        pdf_bytes = validate_file_size_and_format(pdf_file)
        resume_json = await generate_resume_json_from_pdf(pdf_bytes)

        # Serialize the resume_json if it's a dictionary
        if isinstance(resume_json, dict):
            resume_json_str = json.dumps(resume_json)
        else:
            resume_json_str = resume_json

        # Retry the validation once if it fails (Only ONE retry)
        for attempt in range(2):
            try:
                if not resume_json:
                    logger.error(
                        "Failed to generate resume JSON from PDF",
                        extra={"event_type": "resume_generation_error", "user_id": current_user},
                    )
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Failed to generate resume JSON from the PDF.",
                    )
                logger.info(
                    "Resume JSON generated successfully",
                    extra={"event_type": "resume_json_generated", "user_id": current_user},
                )
                return GetResume.model_validate_json(resume_json_str)
            except Exception as validation_error:
                if attempt == 1:
                    logger.error(
                        f"Validation attempt {attempt + 1} failed: {validation_error}",
                        exc_info=True,
                        extra={"event_type": "resume_validation_error", "user_id": current_user},
                    )
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Validation failed for the resume JSON.",
                    )
                logger.warning(
                    f"Validation attempt {attempt + 1} failed, retrying...",
                    extra={"event_type": "resume_validation_retry", "user_id": current_user},
                )

    except Exception as e:
        logger.error(
            "Unexpected error during PDF to JSON conversion: " + str(e),
            exc_info=True,
            extra={"event_type": "unexpected_error", "user_id": current_user, "error_details": str(e)},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while processing the PDF.",
        )