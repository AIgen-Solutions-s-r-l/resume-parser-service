# app/tests/test_main.py
"""
Tests for main FastAPI application configuration and basic endpoints.
"""
import pytest
from fastapi import status

from app.main import app


@pytest.mark.asyncio
class TestMainApplication:
    """Test suite for main FastAPI application configuration and endpoints."""

    async def test_root_endpoint(self, async_client):
        """Test the root endpoint returns correct status and message."""
        response = await async_client.get("/")

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {"message": "ResumeIngestor Service is up and running!"}

    async def test_app_title_and_description(self):
        """Test the application metadata is correctly configured."""
        assert app.title == "Resume Ingestor API"
        assert app.description == "Service for resume ingestion and parsing"
        assert app.version == "1.0.0"

    async def test_cors_middleware_headers(self, async_client):
        """Test CORS middleware is properly configured."""
        origin = "http://localhost:3000"
        headers = {
            "Origin": origin,
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "Content-Type",
        }

        response = await async_client.options("/", headers=headers)

        assert response.status_code == status.HTTP_200_OK
        assert "access-control-allow-origin" in response.headers
        assert response.headers["access-control-allow-origin"] == origin

    @pytest.mark.parametrize(
        "endpoint",
        [
            "/resumes/create_resume",
            "/resumes/get",
            "/resumes/update",
            "/resumes/pdf_to_json",
            "/resumes/exists",
        ],
    )
    async def test_resume_routes_exist(self, async_client, endpoint):
        """Test that all expected resume routes are registered."""
        response = await async_client.options(endpoint)
        assert response.status_code != status.HTTP_404_NOT_FOUND

    async def test_healthcheck_endpoint_exists(self, async_client):
        """Test that healthcheck endpoint is registered."""
        response = await async_client.options("/healthcheck")
        assert response.status_code != status.HTTP_404_NOT_FOUND

    async def test_health_check_headers(self, async_client):
        """Test root endpoint includes correct content-type header."""
        response = await async_client.get("/")

        assert "content-type" in response.headers
        assert response.headers["content-type"] == "application/json"

    @pytest.mark.parametrize(
        "method,endpoint",
        [
            ("GET", "/nonexistent"),
            ("POST", "/invalid"),
            ("PUT", "/unknown"),
        ],
    )
    async def test_404_handler(self, async_client, method, endpoint):
        """Test 404 errors are handled correctly."""
        response = await async_client.request(method, endpoint)

        assert response.status_code == status.HTTP_404_NOT_FOUND
        error_response = response.json()
        assert "detail" in error_response

    async def test_startup_event(self):
        """Test the application has state attribute."""
        assert hasattr(app, "state")

    async def test_validation_error_handler(self, auth_client):
        """Test custom validation error handler returns correct format."""
        response = await auth_client.post(
            "/resumes/create_resume",
            json={
                "invalid_field": "data"  # Missing required fields
            },
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        error_response = response.json()
        assert "error" in error_response
        assert error_response["error"] == "ValidationError"
        assert "message" in error_response
        assert "details" in error_response
