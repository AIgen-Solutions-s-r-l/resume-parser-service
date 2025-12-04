# app/core/auth.py
import logging
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, ExpiredSignatureError

from app.core.security import verify_jwt_token

logger = logging.getLogger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


class AuthenticationError(HTTPException):
    """Base authentication error."""

    def __init__(self, detail: str, status_code: int = status.HTTP_401_UNAUTHORIZED):
        super().__init__(
            status_code=status_code,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(token: str = Depends(oauth2_scheme)) -> int:
    """
    Validate JWT token and extract user ID.

    Args:
        token: JWT Bearer token from request

    Returns:
        User ID as integer

    Raises:
        AuthenticationError: If token is invalid, expired, or missing required claims
    """
    try:
        payload = verify_jwt_token(token)

        user_id = payload.get("id")
        if user_id is None:
            logger.warning(
                "Token missing 'id' claim",
                extra={"event_type": "auth_failure", "reason": "missing_claim"}
            )
            raise AuthenticationError("Token missing required claims")

        return int(user_id)

    except ExpiredSignatureError:
        logger.info(
            "Expired token used",
            extra={"event_type": "auth_failure", "reason": "token_expired"}
        )
        raise AuthenticationError("Token has expired")

    except JWTError as e:
        logger.warning(
            f"Invalid JWT token: {e}",
            extra={"event_type": "auth_failure", "reason": "invalid_token"}
        )
        raise AuthenticationError("Invalid token")

    except ValueError as e:
        logger.warning(
            f"Invalid user_id format: {e}",
            extra={"event_type": "auth_failure", "reason": "invalid_user_id"}
        )
        raise AuthenticationError("Invalid token payload")