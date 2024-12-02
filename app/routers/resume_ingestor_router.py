from typing import Any
from fastapi import APIRouter, HTTPException, Depends, status, UploadFile, File
from io import BytesIO
from PyPDF2 import PdfReader, errors
from app.core.auth import get_current_user
from app.core.logging_config import LogConfig
from app.core.exceptions import InvalidResumeDataError, ResumeNotFoundError
from app.schemas.resume import AddResume, UpdateResume
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
    Validate file size and format. Returns file content if valid.

    Args:
        file (UploadFile): Uploaded file to validate.

    Returns:
        bytes: Content of the uploaded file.

    Raises:
        HTTPException: If file size exceeds the limit or format is invalid.
    """
    file.file.seek(0, 2)
    if file.file.tell() > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size exceeds the 10 MB limit.",
        )
    file.file.seek(0)
    file_bytes = file.file.read()
    try:
        reader = PdfReader(BytesIO(file_bytes))
        _ = reader.pages[0]  # Validate by accessing first page
    except (errors.PdfStreamError, IndexError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file format. Only PDFs are allowed.",
        )
    return file_bytes

@router.post(
    "/create_resume",
    response_model=AddResume,
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"description": "Resume successfully created"},
        400: {"description": "Invalid resume data"},
        404: {"description": "User not found"},
        500: {"description": "Internal server error"},
    },
)
async def create_resume(resume_data: AddResume, current_user=Depends(get_current_user)) -> Any:
    """Create a new resume in the database."""
    result = await add_resume(resume_data, current_user)
    if "error" in result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail={"message": result["error"]}
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
        500: {"description": "Internal server error"},
    },
)
async def get_resume(current_user=Depends(get_current_user)) -> Any:
    """Retrieve a user's resume from the database."""
    try:
        result = await get_resume_by_user_id(current_user)
        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail={"message": result["error"]}
            )
        logger.info("Resume retrieved", extra={"user_id": current_user})
        return result
    except Exception as e:
        logger.error("Error retrieving resume", exc_info=True)
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
        return result
    except ResumeNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail={"message": str(e)}
        )
    except InvalidResumeDataError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail={"message": str(e)}
        )
    except Exception as e:
        logger.error("Error updating resume", exc_info=True)
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
async def pdf_to_json(pdf_file: UploadFile = File(...), current_user=Depends(get_current_user)) -> Any:
    """Convert a PDF resume to JSON."""
    try:
        pdf_bytes = validate_file_size_and_format(pdf_file)
        resume_json = await generate_resume_json_from_pdf(pdf_bytes)
        if not resume_json:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to generate resume JSON from the PDF.",
            )
        return resume_json
    except Exception as e:
        logger.error("Error converting PDF to JSON", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while processing the PDF.",
        )
