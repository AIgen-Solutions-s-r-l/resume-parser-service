import json
from typing import Any
from fastapi import APIRouter, HTTPException, Depends, status, UploadFile, File
from io import BytesIO
from PyPDF2 import PdfReader, errors

from pydantic import ValidationError

from app.core.auth import get_current_user
from app.core.config import settings
from app.core.logging_config import LogConfig
from app.core.exceptions import (
    InvalidResumeDataError,
    ResumeNotFoundError,
    DatabaseOperationError,
)
from app.schemas.resume import UpdateResume, AddResume, GetResume
from app.services.resume_service import (
    get_resume_by_user_id,
    add_resume,
    update_resume,
    generate_resume_json_from_pdf,
)

# Constants
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
ALLOWED_CONTENT_TYPES = {"application/pdf"}
PDF_MAGIC_BYTES = b"%PDF"

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


async def validate_file_size_and_format(file: UploadFile) -> bytes:
    """
    Validate file size, MIME type, and PDF format with streaming support.

    Args:
        file: Uploaded file to validate.

    Returns:
        Content of the uploaded file as bytes.

    Raises:
        HTTPException: If file fails any validation check.
    """
    # Validate content type from header
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        logger.warning(
            "Invalid content type",
            extra={
                "event_type": "file_validation_error",
                "content_type": file.content_type,
                "filename": file.filename,
            },
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Only PDF files are allowed (got {file.content_type}).",
        )

    # Read file with size limit check during streaming
    chunks = []
    total_size = 0

    while True:
        chunk = await file.read(8192)  # 8KB chunks
        if not chunk:
            break

        total_size += len(chunk)
        if total_size > MAX_FILE_SIZE:
            logger.warning(
                "File too large",
                extra={
                    "event_type": "file_size_error",
                    "file_size": total_size,
                    "max_size": MAX_FILE_SIZE,
                },
            )
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File size exceeds the {MAX_FILE_SIZE // (1024 * 1024)} MB limit.",
            )

        chunks.append(chunk)

    file_bytes = b"".join(chunks)

    # Validate PDF magic bytes
    if not file_bytes.startswith(PDF_MAGIC_BYTES):
        logger.warning(
            "Invalid PDF magic bytes",
            extra={"event_type": "file_validation_error", "filename": file.filename},
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file format. File does not appear to be a valid PDF.",
        )

    # Validate PDF structure
    try:
        pdf_reader = PdfReader(BytesIO(file_bytes))
        if len(pdf_reader.pages) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="PDF file contains no pages.",
            )
        logger.info(
            "File validated successfully",
            extra={
                "event_type": "file_validation",
                "filename": file.filename,
                "size": total_size,
                "pages": len(pdf_reader.pages),
            },
        )
    except errors.PdfStreamError as e:
        logger.warning(
            "Invalid PDF structure",
            extra={
                "event_type": "file_format_error",
                "filename": file.filename,
                "error": str(e),
            },
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid PDF file. The file structure is corrupted.",
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
    logger.info(
        "Attempting to add resume to the database",
        extra={"event_type": "database_operation_start", "user_id": current_user},
    )

    try:
        result = await add_resume(resume_data, current_user)
    except DatabaseOperationError as e:
        logger.error(
            "Database error during resume creation",
            extra={"event_type": "database_error", "user_id": current_user, "error": str(e)},
        )
        raise

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
    except DatabaseOperationError as e:
        logger.error(
            "Database error during resume retrieval",
            extra={"event_type": "database_error", "user_id": current_user, "error": str(e)},
        )
        raise

    if "error" in result:
        logger.warning(
            "Resume not found",
            extra={"event_type": "resume_not_found", "user_id": current_user},
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail={"message": result["error"]}
        )

    logger.info(
        "Resume retrieved",
        extra={"event_type": "resume_retrieved", "user_id": current_user},
    )
    return result

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
    except ResumeNotFoundError as e:
        logger.warning(
            "Resume not found during update",
            extra={"event_type": "resume_not_found", "user_id": current_user, "error": str(e)},
        )
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"message": str(e)})
    except InvalidResumeDataError as e:
        logger.warning(
            "Invalid resume data during update",
            extra={"event_type": "invalid_resume_data", "user_id": current_user, "error": str(e)},
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"message": str(e)})
    except DatabaseOperationError as e:
        logger.error(
            "Database error during resume update",
            extra={"event_type": "database_error", "user_id": current_user, "error": str(e)},
        )
        raise

    logger.info(
        "Resume updated",
        extra={"event_type": "resume_updated", "user_id": current_user},
    )
    return result

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
    pdf_bytes = await validate_file_size_and_format(pdf_file)
    resume_json = await generate_resume_json_from_pdf(pdf_bytes)

    if not resume_json:
        logger.error(
            "Failed to generate resume JSON from PDF",
            extra={"event_type": "resume_generation_error", "user_id": current_user},
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to generate resume JSON from the PDF.",
        )

    # Serialize the resume_json if it's a dictionary
    if isinstance(resume_json, dict):
        resume_json_str = json.dumps(resume_json)
    else:
        resume_json_str = resume_json

    # Retry validation once if it fails
    last_error = None
    for attempt in range(2):
        try:
            result = GetResume.model_validate_json(resume_json_str)
            logger.info(
                "Resume JSON generated successfully",
                extra={"event_type": "resume_json_generated", "user_id": current_user},
            )
            return result
        except ValidationError as e:
            last_error = e
            if attempt == 0:
                logger.warning(
                    f"Validation attempt {attempt + 1} failed, retrying...",
                    extra={"event_type": "resume_validation_retry", "user_id": current_user},
                )
            continue

    logger.error(
        f"Validation failed after retries: {last_error}",
        extra={"event_type": "resume_validation_error", "user_id": current_user},
    )
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Validation failed for the resume JSON.",
    )
    
@router.get(
    "/exists",
    responses={
        200: {"description": "Whether or not a user's resume exists."},
        401: {"description": "Not authenticated"},
        500: {"description": "Internal server error"},
    },
)
async def check_resume_exists(current_user=Depends(get_current_user)) -> Any:
    """
    Check if the authenticated user has a resume.

    Returns:
        Dict with "exists" boolean indicating if the user's resume is present.
    """
    logger.info(
        "Checking if user has a resume",
        extra={"event_type": "check_resume_exists", "user_id": current_user},
    )

    try:
        from app.services.resume_service import user_has_resume
        exists = await user_has_resume(current_user)
        return {"exists": exists}
    except DatabaseOperationError as e:
        logger.error(
            "Database error during resume existence check",
            extra={"event_type": "database_error", "user_id": current_user, "error": str(e)},
        )
        raise