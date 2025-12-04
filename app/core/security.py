# app/core/security.py
import bcrypt
from datetime import datetime, timedelta, timezone
from typing import Literal, Optional

from jose import jwt

from app.core.config import settings

# Token types
TOKEN_TYPE_ACCESS = "access"
TOKEN_TYPE_REFRESH = "refresh"


def get_password_hash(password: str) -> str:
    """
    Generate password hash using bcrypt.

    Args:
        password: Plain text password

    Returns:
        Hashed password as string
    """
    salt = bcrypt.gensalt()
    password_bytes = password.encode("utf-8")
    return bcrypt.hashpw(password_bytes, salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify password against hash using bcrypt.

    Args:
        plain_password: Password to verify
        hashed_password: Hash to verify against

    Returns:
        True if password matches hash
    """
    password_bytes = plain_password.encode("utf-8")
    hashed_bytes = hashed_password.encode("utf-8")
    return bcrypt.checkpw(password_bytes, hashed_bytes)


def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None,
    token_type: Literal["access", "refresh"] = TOKEN_TYPE_ACCESS,
) -> str:
    """
    Create JWT access token.

    Args:
        data: Data to encode in token
        expires_delta: Optional expiration time
        token_type: Type of token (access or refresh)

    Returns:
        JWT token string
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.access_token_expire_minutes
        )

    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": token_type,
    })

    encoded_jwt = jwt.encode(
        to_encode, settings.secret_key, algorithm=settings.algorithm
    )
    return encoded_jwt


def verify_jwt_token(
    token: str,
    expected_type: Optional[Literal["access", "refresh"]] = TOKEN_TYPE_ACCESS,
) -> dict:
    """
    Verify JWT token and optionally validate token type.

    Args:
        token: Token to verify
        expected_type: Expected token type. If provided, validates the type claim.

    Returns:
        Decoded token data

    Raises:
        JWTError: If token is invalid or expired
        ValueError: If token type doesn't match expected type
    """
    # Decode and verify signature + expiration
    payload = jwt.decode(
        token,
        settings.secret_key,
        algorithms=[settings.algorithm],
        options={"require_exp": True},
    )

    # Validate token type if expected
    if expected_type:
        token_type = payload.get("type")
        if token_type != expected_type:
            raise ValueError(
                f"Invalid token type: expected '{expected_type}', got '{token_type}'"
            )

    return payload