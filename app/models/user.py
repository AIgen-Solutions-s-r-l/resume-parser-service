"""Pydantic models for user-related data including User and PasswordResetToken."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field

class User(BaseModel):
    """
    Pydantic model representing a user.

    Attributes:
        id (str): The MongoDB ObjectId for the user.
        username (str): Unique username for the user.
        email (str): Unique email for the user.
        hashed_password (str): Hashed password for the user.
        is_admin (bool): Flag indicating if user has admin privileges.
    """
    id: Optional[str] = Field(None, alias="_id")
    username: str
    email: EmailStr
    hashed_password: str
    is_admin: bool = False

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "username": "johndoe",
                "email": "john@example.com",
                "hashed_password": "hashedpassword123",
                "is_admin": False
            }
        }


class PasswordResetToken(BaseModel):
    """
    Pydantic model representing a password reset token.
    
    Attributes:
        token (str): The unique token string used for password reset.
        user_id (str): Reference to the user requesting reset.
        expires_at (datetime): Timestamp when the token expires.
        used (bool): Flag indicating if token has been used.
    """
    token: str
    user_id: str
    expires_at: datetime
    used: bool = False

    class Config:
        json_schema_extra = {
            "example": {
                "token": "reset-token-123",
                "user_id": "user-id-123",
                "expires_at": "2024-02-04T12:00:00Z",
                "used": False
            }
        }
