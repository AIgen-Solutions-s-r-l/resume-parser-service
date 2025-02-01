# tests/test_main.py

from typing import Generator

import pytest
from fastapi import HTTPException, status, APIRouter
from fastapi.routing import APIRoute
from httpx import AsyncClient

from app.core.exceptions import AuthException, UserAlreadyExistsError
from app.main import app

from unittest.mock import patch, AsyncMock

from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.auth import get_current_user
from app.core.database import get_db
from app.models.user import User, Base

TEST_DATABASE_URL = "postgresql+asyncpg://testuser:testpassword@localhost:5432/test_db"


# Fixture per il client di test
@pytest.fixture
async def async_client() -> Generator:
    from httpx import AsyncClient
    async with AsyncClient(
            app=app,
            base_url="http://test",
            follow_redirects=True
    ) as client:
        yield client
        

@pytest.fixture(scope="session")
async def test_engine():
    """Create test database engine."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture(scope="function")
async def test_db_session(test_engine):
    """Provide test database session."""
    TestingSessionLocal = sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False
    )

    async with TestingSessionLocal() as session:
        try:
            yield session
        finally:
            await session.rollback()
            await session.close()


@pytest.fixture(scope="function")
async def client(test_db_session):
    """Create test client with overridden database session."""
    app.dependency_overrides.clear()
    app.dependency_overrides[get_db] = lambda: test_db_session

    # Use explicit ASGITransport
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac

    app.dependency_overrides.clear()

@pytest.fixture(scope="function")
async def test_user(test_db_session):
    """Create and provide a test user."""
    from app.core.security import get_password_hash

    test_user = User(
        username="testuser",
        email="test@example.com",
        hashed_password=get_password_hash("testpassword123"),
        is_admin=False
    )

    test_db_session.add(test_user)
    await test_db_session.commit()
    await test_db_session.refresh(test_user)

    try:
        yield test_user
    finally:
        await test_db_session.delete(test_user)
        await test_db_session.commit()
        
@pytest.fixture(scope="function")
async def auth_client(client, test_user):
    """Create authenticated test client."""
    from app.core.security import create_access_token

    # Create access token
    access_token = create_access_token(data={"sub": test_user.username})

    # Override both the database and auth dependencies
    async def override_get_current_user():
        return test_user

    app.dependency_overrides[get_current_user] = override_get_current_user
    client.headers["Authorization"] = f"Bearer {access_token}"

    try:
        yield client
    finally:
        # Clean up overrides after test
        app.dependency_overrides.clear()


@pytest.mark.asyncio
class TestMainApplication:
    """Test suite for main FastAPI application configuration and endpoints."""

    async def test_root_endpoint(self, async_client: AsyncClient):
        """Test the root endpoint returns correct status and message."""
        response = await async_client.get("/")
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {"message": "ResumeIngestor Service is up and running!"}

    async def test_app_title_and_description(self):
        """Test the application metadata is correctly configured."""
        assert app.title == "Resume Ingestor API"
        assert app.description == "Service for resume ingestion and parsing"
        assert app.version == "1.0.0"

    async def test_cors_middleware_headers(self, async_client: AsyncClient):
        """Test CORS middleware is properly configured."""
        origin = "http://localhost:3000"
        headers = {
            "Origin": origin,
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "Content-Type"
        }
        response = await async_client.options(
            "/",
            headers=headers,
        )

        assert response.status_code == status.HTTP_200_OK, f"Response: {response.text}"
        assert "access-control-allow-origin" in response.headers
        assert response.headers["access-control-allow-origin"] == origin
        assert "access-control-allow-methods" in response.headers
        assert "GET" in response.headers["access-control-allow-methods"]

    @pytest.mark.parametrize("endpoint", [
        "/resumes/create_resume"
    ])
    async def test_routes_exist(self, async_client: AsyncClient, endpoint: str):
        """Test that all expected routes are registered."""
        response = await async_client.options(endpoint)
        assert response.status_code != status.HTTP_404_NOT_FOUND

    async def test_validation_error_handler(self, auth_client: AsyncClient):
        """Test custom validation error handler returns correct format."""
        # Try to register with invalid data to trigger validation error
        response = await auth_client.post("/resumes/create_resume", json={
            "username": "",  # Invalid empty username
            "email": "not-an-email",  # Invalid email format
            "password": ""  # Invalid empty password
        })
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        error_response = response.json()
        assert "error" in error_response
        assert error_response["error"] == "ValidationError"
        assert "message" in error_response
        assert "details" in error_response

    test_router = None  # Variabile di classe per tenere traccia del router di test

    @pytest.mark.parametrize("exception_class,expected_status", [
        (UserAlreadyExistsError("test"), status.HTTP_409_CONFLICT),
        (AuthException("test", status.HTTP_401_UNAUTHORIZED), status.HTTP_401_UNAUTHORIZED),
        (HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="test"), status.HTTP_404_NOT_FOUND)
    ])
    async def test_exception_handlers(
            self,
            async_client: AsyncClient,
            exception_class: Exception,
            expected_status: int
    ):
        """Test custom exception handlers return correct status codes and formats."""

        # Rimuovi il router precedente se esiste
        if self.test_router:
            app.routes = [r for r in app.routes if r not in self.test_router.routes]

        # Crea un nuovo router con un path unico
        self.test_router = APIRouter()

        @self.test_router.get(f"/test-{expected_status}")
        async def test_route():
            raise exception_class

        app.include_router(self.test_router)

        response = await async_client.get(f"/test-{expected_status}")
        assert response.status_code == expected_status
        assert "detail" in response.json()

    @classmethod
    async def cleanup(cls):
        """Cleanup method to remove test routes"""
        if cls.test_router:
            app.routes = [r for r in app.routes if r not in cls.test_router.routes]
            cls.test_router = None

    async def test_health_check_headers(self, async_client: AsyncClient):
        """Test health check endpoint includes necessary headers."""
        response = await async_client.get("/")
        assert "content-type" in response.headers
        assert response.headers["content-type"] == "application/json"

    @pytest.mark.parametrize("method,endpoint", [
        ("GET", "/nonexistent"),
        ("POST", "/invalid"),
        ("PUT", "/unknown")
    ])
    async def test_404_handler(self, async_client: AsyncClient, method: str, endpoint: str):
        """Test 404 errors are handled correctly."""
        response = await async_client.request(method, endpoint)
        assert response.status_code == status.HTTP_404_NOT_FOUND
        error_response = response.json()
        assert "detail" in error_response

    async def test_startup_event(self):
        """Test the application startup event handler."""
        # This depends on what you have in your startup event
        # For example, if you're initializing RabbitMQ:
        assert hasattr(app, "state")
        # Add more assertions based on what your startup event does

    async def test_shutdown_event(self):
        """Test the application shutdown event handler."""
        # This depends on what you have in your shutdown event
        # For example, if you're closing connections:
        # Add assertions based on what your shutdown event does
        pass


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
