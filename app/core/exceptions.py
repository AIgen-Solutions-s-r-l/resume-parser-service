# app/core/exceptions.py
"""
Centralized exception definitions with consistent error response format.

All API errors follow this format:
{
    "error": "ErrorClassName",
    "message": "Human-readable error description"
}
"""
from typing import Any, Dict, Optional

from fastapi import HTTPException, status
from pydantic import BaseModel


class ErrorResponse(BaseModel):
    """Standard error response schema for API documentation."""

    error: str
    message: str


def create_error_detail(error_type: str, message: str) -> Dict[str, Any]:
    """Create a standardized error detail dictionary."""
    return {"error": error_type, "message": message}


# =============================================================================
# Base Exception Classes
# =============================================================================


class APIException(HTTPException):
    """Base exception for all API errors with consistent format."""

    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        error_type: Optional[str] = None,
    ):
        error_name = error_type or self.__class__.__name__
        super().__init__(
            status_code=status_code,
            detail=create_error_detail(error_name, message),
        )


# =============================================================================
# Authentication Exceptions
# =============================================================================


class AuthException(APIException):
    """Base exception for authentication errors."""

    pass


class UserAlreadyExistsError(AuthException):
    """Raised when attempting to register a user that already exists."""

    def __init__(self, identifier: str):
        super().__init__(
            message=f"User with identifier '{identifier}' already exists",
            status_code=status.HTTP_409_CONFLICT,
        )


class InvalidCredentialsError(AuthException):
    """Raised when login credentials are invalid."""

    def __init__(self):
        super().__init__(
            message="Invalid credentials",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )


class UserNotFoundError(AuthException):
    """Raised when a user is not found."""

    def __init__(self, identifier: str):
        super().__init__(
            message=f"User with identifier '{identifier}' not found",
            status_code=status.HTTP_404_NOT_FOUND,
        )


# =============================================================================
# Resume Exceptions
# =============================================================================


class ResumeException(APIException):
    """Base exception for resume-related errors."""

    pass


class ResumeNotFoundError(ResumeException):
    """Raised when a resume cannot be found."""

    def __init__(self, detail: str = ""):
        message = f"Resume not found: {detail}" if detail else "Resume not found"
        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
        )


class InvalidResumeDataError(ResumeException):
    """Raised when resume data is invalid."""

    def __init__(self, detail: str):
        super().__init__(
            message=f"Invalid resume data: {detail}",
            status_code=status.HTTP_400_BAD_REQUEST,
        )


class ResumeDuplicateError(ResumeException):
    """Raised when attempting to create a duplicate resume."""

    def __init__(self, user_id: int):
        super().__init__(
            message=f"Resume already exists for user_id: {user_id}",
            status_code=status.HTTP_409_CONFLICT,
        )


class ResumeValidationError(ResumeException):
    """Raised when resume data fails validation."""

    def __init__(self, detail: str):
        super().__init__(
            message=f"Resume validation failed: {detail}",
            status_code=status.HTTP_400_BAD_REQUEST,
        )


# =============================================================================
# Database Exceptions
# =============================================================================


class DatabaseOperationError(APIException):
    """Raised when a database operation fails."""

    def __init__(self, detail: str):
        super().__init__(
            message=f"Database operation failed: {detail}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


# =============================================================================
# File Processing Exceptions
# =============================================================================


class FileProcessingError(APIException):
    """Raised when file processing fails."""

    def __init__(self, detail: str):
        super().__init__(
            message=f"File processing failed: {detail}",
            status_code=status.HTTP_400_BAD_REQUEST,
        )


class FileTooLargeError(APIException):
    """Raised when uploaded file exceeds size limit."""

    def __init__(self, max_size_mb: int):
        super().__init__(
            message=f"File size exceeds the {max_size_mb} MB limit",
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
        )


class InvalidFileTypeError(APIException):
    """Raised when file type is not allowed."""

    def __init__(self, allowed_types: str = "PDF"):
        super().__init__(
            message=f"Invalid file type. Only {allowed_types} files are allowed",
            status_code=status.HTTP_400_BAD_REQUEST,
        )
