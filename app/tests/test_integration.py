# app/tests/test_integration.py
"""
Integration tests with real MongoDB using testcontainers.

These tests require Docker to be available and will spin up a real MongoDB
container for testing database operations end-to-end.
"""
import asyncio
from typing import AsyncGenerator, Generator

import pytest
from httpx import ASGITransport, AsyncClient
from motor.motor_asyncio import AsyncIOMotorClient

from app.core.auth import get_current_user
from app.core.dependencies import DatabaseManager
from app.core.security import create_access_token
from app.main import app

# Skip all tests in this module if testcontainers is not available
pytest.importorskip("testcontainers")

from testcontainers.mongodb import MongoDbContainer


# =============================================================================
# MongoDB Container Fixtures
# =============================================================================


@pytest.fixture(scope="module")
def mongodb_container() -> Generator[MongoDbContainer, None, None]:
    """
    Start a MongoDB container for the test module.

    This container is shared across all tests in the module for efficiency.
    """
    with MongoDbContainer("mongo:7.0") as mongo:
        yield mongo


@pytest.fixture(scope="module")
def mongodb_url(mongodb_container: MongoDbContainer) -> str:
    """Get the MongoDB connection URL from the container."""
    return mongodb_container.get_connection_url()


@pytest.fixture(scope="module")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an event loop for the module."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


@pytest.fixture
async def test_db(mongodb_url: str) -> AsyncGenerator[AsyncIOMotorClient, None]:
    """
    Create a test database client.

    Each test gets a fresh database that is cleaned up after the test.
    """
    client = AsyncIOMotorClient(mongodb_url)
    db = client["test_resumes"]

    yield db

    # Cleanup: drop all collections after each test
    collections = await db.list_collection_names()
    for collection in collections:
        await db.drop_collection(collection)

    client.close()


@pytest.fixture
async def integration_client(
    mongodb_url: str, test_db
) -> AsyncGenerator[AsyncClient, None]:
    """
    Create an async client with real MongoDB connection.

    Overrides the DatabaseManager to use the test container.
    """
    # Create a custom database manager for testing
    test_db_manager = DatabaseManager()
    test_db_manager._client = AsyncIOMotorClient(mongodb_url)
    test_db_manager._database = test_db_manager._client["test_resumes"]
    test_db_manager._is_connected = True

    # Override the singleton
    original_instance = DatabaseManager._instance
    DatabaseManager._instance = test_db_manager

    # Override auth to return test user
    async def override_get_current_user() -> int:
        return 12345

    app.dependency_overrides[get_current_user] = override_get_current_user

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        follow_redirects=True,
    ) as client:
        # Add auth header
        token = create_access_token(data={"id": 12345})
        client.headers["Authorization"] = f"Bearer {token}"
        yield client

    # Restore
    app.dependency_overrides.clear()
    DatabaseManager._instance = original_instance
    test_db_manager._client.close()


# =============================================================================
# Integration Tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.integration
class TestResumeIntegration:
    """Integration tests for resume CRUD operations."""

    async def test_create_resume_integration(self, integration_client: AsyncClient):
        """Test creating a resume with real database."""
        resume_data = {
            "personal_information": {
                "name": "Integration",
                "surname": "Test",
                "email": "integration@test.com",
            },
            "education_details": [],
            "experience_details": [],
            "projects": [],
            "achievements": [],
            "certifications": [],
            "languages": [],
            "interests": [],
            "availability": {},
            "salary_expectations": {},
            "self_identification": {},
            "legal_authorization": {},
            "work_preferences": {},
        }

        response = await integration_client.post(
            "/resumes/create_resume",
            json=resume_data,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["personal_information"]["name"] == "Integration"
        assert data["user_id"] == 12345

    async def test_get_resume_integration(self, integration_client: AsyncClient):
        """Test getting a resume after creation."""
        # First create a resume
        resume_data = {
            "personal_information": {
                "name": "Get",
                "surname": "Test",
                "email": "get@test.com",
            },
            "education_details": [],
            "experience_details": [],
            "projects": [],
            "achievements": [],
            "certifications": [],
            "languages": [],
            "interests": [],
            "availability": {},
            "salary_expectations": {},
            "self_identification": {},
            "legal_authorization": {},
            "work_preferences": {},
        }

        create_response = await integration_client.post(
            "/resumes/create_resume",
            json=resume_data,
        )
        assert create_response.status_code == 201

        # Now get it
        get_response = await integration_client.get("/resumes/get")

        assert get_response.status_code == 200
        data = get_response.json()
        assert data["personal_information"]["name"] == "Get"

    async def test_update_resume_integration(self, integration_client: AsyncClient):
        """Test updating a resume."""
        # Create initial resume
        resume_data = {
            "personal_information": {
                "name": "Original",
                "surname": "Name",
                "email": "original@test.com",
            },
            "education_details": [],
            "experience_details": [],
            "projects": [],
            "achievements": [],
            "certifications": [],
            "languages": [],
            "interests": [],
            "availability": {},
            "salary_expectations": {},
            "self_identification": {},
            "legal_authorization": {},
            "work_preferences": {},
        }

        await integration_client.post("/resumes/create_resume", json=resume_data)

        # Update it
        updated_data = resume_data.copy()
        updated_data["personal_information"]["name"] = "Updated"

        update_response = await integration_client.put(
            "/resumes/update",
            json=updated_data,
        )

        assert update_response.status_code == 200
        data = update_response.json()
        assert data["personal_information"]["name"] == "Updated"

    async def test_resume_exists_integration(self, integration_client: AsyncClient):
        """Test checking if resume exists."""
        # Initially should not exist (fresh test)
        exists_response = await integration_client.get("/resumes/exists")
        # Note: Due to fixture isolation, this might vary based on test order

        # Create a resume
        resume_data = {
            "personal_information": {
                "name": "Exists",
                "surname": "Test",
                "email": "exists@test.com",
            },
            "education_details": [],
            "experience_details": [],
            "projects": [],
            "achievements": [],
            "certifications": [],
            "languages": [],
            "interests": [],
            "availability": {},
            "salary_expectations": {},
            "self_identification": {},
            "legal_authorization": {},
            "work_preferences": {},
        }

        await integration_client.post("/resumes/create_resume", json=resume_data)

        # Now should exist
        exists_response = await integration_client.get("/resumes/exists")
        assert exists_response.status_code == 200
        assert exists_response.json()["exists"] is True

    async def test_resume_not_found_integration(self, integration_client: AsyncClient):
        """Test 404 when resume doesn't exist."""
        # Override to use a different user ID with no resume
        async def override_no_resume_user() -> int:
            return 99999

        app.dependency_overrides[get_current_user] = override_no_resume_user

        response = await integration_client.get("/resumes/get")

        assert response.status_code == 404

        # Restore original override
        async def override_get_current_user() -> int:
            return 12345

        app.dependency_overrides[get_current_user] = override_get_current_user


@pytest.mark.asyncio
@pytest.mark.integration
class TestHealthCheckIntegration:
    """Integration tests for health check endpoints."""

    async def test_healthcheck_with_db(self, integration_client: AsyncClient):
        """Test health check returns healthy with real DB."""
        response = await integration_client.get("/healthcheck")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    async def test_readiness_with_db(self, integration_client: AsyncClient):
        """Test readiness probe with real DB."""
        response = await integration_client.get("/ready")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"

    async def test_liveness(self, integration_client: AsyncClient):
        """Test liveness probe (doesn't need DB)."""
        response = await integration_client.get("/live")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "alive"

    async def test_cache_metrics(self, integration_client: AsyncClient):
        """Test cache metrics endpoint."""
        response = await integration_client.get("/metrics/cache")

        assert response.status_code == 200
        data = response.json()
        assert "hits" in data
        assert "misses" in data
        assert "hit_ratio" in data
