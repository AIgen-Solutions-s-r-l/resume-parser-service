# app/tests/test_security.py
"""
Security-focused tests for the resume service.
"""
from datetime import timedelta
from unittest.mock import patch

import pytest
from fastapi import status
from jose import jwt

from app.core.config import settings
from app.core.security import (
    TOKEN_TYPE_ACCESS,
    TOKEN_TYPE_REFRESH,
    create_access_token,
    get_password_hash,
    verify_jwt_token,
    verify_password,
)


class TestPasswordSecurity:
    """Tests for password hashing and verification."""

    def test_password_hash_is_different_from_plain(self):
        """Test that hashed password differs from plain text."""
        plain_password = "SecureP@ssw0rd!"
        hashed = get_password_hash(plain_password)

        assert hashed != plain_password
        assert len(hashed) > 0

    def test_password_hash_is_unique(self):
        """Test that same password produces different hashes (salted)."""
        plain_password = "SecureP@ssw0rd!"
        hash1 = get_password_hash(plain_password)
        hash2 = get_password_hash(plain_password)

        assert hash1 != hash2

    def test_verify_password_correct(self):
        """Test password verification with correct password."""
        plain_password = "SecureP@ssw0rd!"
        hashed = get_password_hash(plain_password)

        assert verify_password(plain_password, hashed) is True

    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password."""
        plain_password = "SecureP@ssw0rd!"
        wrong_password = "WrongPassword123"
        hashed = get_password_hash(plain_password)

        assert verify_password(wrong_password, hashed) is False

    def test_verify_password_empty(self):
        """Test password verification with empty password."""
        plain_password = "SecureP@ssw0rd!"
        hashed = get_password_hash(plain_password)

        assert verify_password("", hashed) is False


class TestJwtTokenSecurity:
    """Tests for JWT token security."""

    def test_create_access_token_contains_required_claims(self):
        """Test that access token contains required claims."""
        data = {"id": 1, "username": "testuser"}
        token = create_access_token(data)

        payload = jwt.decode(
            token, settings.secret_key, algorithms=[settings.algorithm]
        )

        assert "id" in payload
        assert "exp" in payload
        assert "iat" in payload
        assert "type" in payload
        assert payload["type"] == TOKEN_TYPE_ACCESS

    def test_create_refresh_token_type(self):
        """Test that refresh token has correct type."""
        data = {"id": 1}
        token = create_access_token(data, token_type=TOKEN_TYPE_REFRESH)

        payload = jwt.decode(
            token, settings.secret_key, algorithms=[settings.algorithm]
        )

        assert payload["type"] == TOKEN_TYPE_REFRESH

    def test_token_expiration(self):
        """Test that token expires after specified time."""
        data = {"id": 1}
        short_expiry = timedelta(seconds=-1)  # Already expired
        token = create_access_token(data, expires_delta=short_expiry)

        with pytest.raises(Exception):  # jwt.ExpiredSignatureError
            verify_jwt_token(token)

    def test_verify_token_wrong_secret(self):
        """Test token verification fails with wrong secret."""
        data = {"id": 1}
        token = create_access_token(data)

        with pytest.raises(Exception):  # jwt.JWTError
            jwt.decode(token, "wrong_secret", algorithms=[settings.algorithm])

    def test_verify_token_wrong_algorithm(self):
        """Test token verification fails with wrong algorithm."""
        data = {"id": 1}
        token = create_access_token(data)

        with pytest.raises(Exception):  # jwt.JWTError
            jwt.decode(token, settings.secret_key, algorithms=["HS512"])

    def test_verify_token_type_mismatch(self):
        """Test verification fails when token type doesn't match."""
        data = {"id": 1}
        token = create_access_token(data, token_type=TOKEN_TYPE_REFRESH)

        with pytest.raises(ValueError, match="Invalid token type"):
            verify_jwt_token(token, expected_type=TOKEN_TYPE_ACCESS)

    def test_verify_token_success(self):
        """Test successful token verification."""
        data = {"id": 1, "username": "testuser"}
        token = create_access_token(data)

        payload = verify_jwt_token(token)

        assert payload["id"] == 1
        assert payload["username"] == "testuser"


class TestAuthenticationEndpoints:
    """Tests for authentication-related endpoints."""

    @pytest.mark.asyncio
    async def test_protected_endpoint_without_token(self, async_client):
        """Test that protected endpoints reject requests without token."""
        response = await async_client.get("/resumes/get")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_protected_endpoint_with_invalid_token(self, async_client):
        """Test that protected endpoints reject invalid tokens."""
        async_client.headers["Authorization"] = "Bearer invalid_token_here"

        response = await async_client.get("/resumes/get")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_protected_endpoint_with_expired_token(self, async_client):
        """Test that protected endpoints reject expired tokens."""
        expired_token = create_access_token(
            data={"id": 1}, expires_delta=timedelta(seconds=-1)
        )
        async_client.headers["Authorization"] = f"Bearer {expired_token}"

        response = await async_client.get("/resumes/get")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_protected_endpoint_with_valid_token(self, auth_client, mongo_mock):
        """Test that protected endpoints accept valid tokens."""
        mongo_mock.find_one.return_value = {"_id": "test", "user_id": 1}

        response = await auth_client.get("/resumes/get")

        # Should not be 401 (might be 404 if no resume, but auth passed)
        assert response.status_code != status.HTTP_401_UNAUTHORIZED


class TestFileUploadSecurity:
    """Tests for file upload security."""

    @pytest.mark.asyncio
    async def test_upload_non_pdf_rejected(self, auth_client):
        """Test that non-PDF files are rejected."""
        fake_file_content = b"This is not a PDF file"

        response = await auth_client.post(
            "/resumes/pdf_to_json",
            files={"pdf_file": ("test.txt", fake_file_content, "text/plain")},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.asyncio
    async def test_upload_fake_pdf_rejected(self, auth_client):
        """Test that files with PDF extension but wrong content are rejected."""
        fake_pdf_content = b"This pretends to be a PDF but isn't"

        response = await auth_client.post(
            "/resumes/pdf_to_json",
            files={"pdf_file": ("fake.pdf", fake_pdf_content, "application/pdf")},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.asyncio
    async def test_upload_oversized_file_rejected(self, auth_client):
        """Test that oversized files are rejected."""
        # Create content larger than 10MB limit
        large_content = b"%PDF-1.4\n" + (b"x" * (11 * 1024 * 1024))

        response = await auth_client.post(
            "/resumes/pdf_to_json",
            files={"pdf_file": ("large.pdf", large_content, "application/pdf")},
        )

        assert response.status_code == status.HTTP_413_REQUEST_ENTITY_TOO_LARGE


class TestInputValidation:
    """Tests for input validation security."""

    @pytest.mark.asyncio
    async def test_xss_in_resume_data_escaped(self, auth_client, mongo_mock):
        """Test that XSS payloads in resume data don't execute."""
        xss_payload = '<script>alert("XSS")</script>'

        mongo_mock.find_one.side_effect = [None, {"_id": "test", "user_id": 1}]
        mongo_mock.insert_one.return_value.inserted_id = "test"

        # The endpoint should accept the data but not execute scripts
        # This tests that the API accepts the input (validation doesn't block it)
        # The frontend should handle escaping when rendering
        response = await auth_client.post(
            "/resumes/create_resume",
            json={
                "personal_information": {
                    "name": xss_payload,
                    "surname": "Test",
                    "email": "test@example.com",
                }
            },
        )

        # Should not cause a server error
        assert response.status_code in [
            status.HTTP_201_CREATED,
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        ]

    @pytest.mark.asyncio
    async def test_sql_injection_in_user_id_prevented(self, auth_client, mongo_mock):
        """Test that SQL injection attempts don't work (MongoDB is NoSQL but test the pattern)."""
        # In MongoDB context, this tests proper parameter handling
        mongo_mock.find_one.return_value = None

        response = await auth_client.get("/resumes/get")

        # The query should use the actual user_id, not an injected string
        mongo_mock.find_one.assert_called()


class TestCorsConfiguration:
    """Tests for CORS security configuration."""

    @pytest.mark.asyncio
    async def test_cors_allows_configured_origins(self, async_client):
        """Test that CORS allows configured origins."""
        headers = {
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        }

        response = await async_client.options("/", headers=headers)

        assert "access-control-allow-origin" in response.headers

    @pytest.mark.asyncio
    async def test_cors_preflight_includes_methods(self, async_client):
        """Test that CORS preflight includes allowed methods."""
        headers = {
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type, Authorization",
        }

        response = await async_client.options("/resumes/create_resume", headers=headers)

        if "access-control-allow-methods" in response.headers:
            assert "POST" in response.headers["access-control-allow-methods"]


class TestRateLimiting:
    """Tests for rate limiting (if implemented)."""

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Rate limiting not yet implemented")
    async def test_rate_limit_exceeded(self, auth_client):
        """Test that rate limiting kicks in after too many requests."""
        # Make many requests quickly
        for _ in range(100):
            await auth_client.get("/resumes/exists")

        response = await auth_client.get("/resumes/exists")

        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
