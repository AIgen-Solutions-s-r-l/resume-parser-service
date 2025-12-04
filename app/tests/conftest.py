# app/tests/conftest.py
"""
Pytest configuration and shared fixtures for all tests.
"""
import asyncio
from dataclasses import dataclass
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient

from app.core.auth import get_current_user
from app.core.security import create_access_token
from app.main import app


def pytest_configure(config):
    """Configure pytest."""
    config.addinivalue_line(
        "markers",
        "asyncio: mark test as async test",
    )


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


# =============================================================================
# User Fixtures
# =============================================================================


@dataclass
class MockUser:
    """Mock user for testing."""
    id: int
    username: str
    email: str
    is_admin: bool = False


@pytest.fixture
def test_user() -> MockUser:
    """Create a standard test user."""
    return MockUser(
        id=1,
        username="testuser",
        email="testuser@example.com",
        is_admin=False,
    )


@pytest.fixture
def test_admin_user() -> MockUser:
    """Create an admin test user."""
    return MockUser(
        id=2,
        username="adminuser",
        email="admin@example.com",
        is_admin=True,
    )


# =============================================================================
# Client Fixtures
# =============================================================================


@pytest.fixture
def sync_client() -> Generator[TestClient, None, None]:
    """Create a synchronous test client."""
    with TestClient(app) as client:
        yield client


@pytest.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Create an async test client."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        follow_redirects=True,
    ) as client:
        yield client


@pytest.fixture
async def auth_client(
    async_client: AsyncClient, test_user: MockUser
) -> AsyncGenerator[AsyncClient, None]:
    """Create an authenticated async test client."""
    access_token = create_access_token(data={"id": test_user.id})

    async def override_get_current_user() -> int:
        return test_user.id

    app.dependency_overrides[get_current_user] = override_get_current_user
    async_client.headers["Authorization"] = f"Bearer {access_token}"

    try:
        yield async_client
    finally:
        app.dependency_overrides.clear()


@pytest.fixture
async def admin_client(
    async_client: AsyncClient, test_admin_user: MockUser
) -> AsyncGenerator[AsyncClient, None]:
    """Create an authenticated admin async test client."""
    access_token = create_access_token(data={"id": test_admin_user.id})

    async def override_get_current_user() -> int:
        return test_admin_user.id

    app.dependency_overrides[get_current_user] = override_get_current_user
    async_client.headers["Authorization"] = f"Bearer {access_token}"

    try:
        yield async_client
    finally:
        app.dependency_overrides.clear()


# =============================================================================
# MongoDB Mock Fixtures
# =============================================================================


@pytest.fixture
def mongo_mock():
    """Mock MongoDB collection for testing."""
    with patch("app.services.resume_service.collection_name") as mock:
        mock.find_one = AsyncMock()
        mock.insert_one = AsyncMock()
        mock.find_one_and_update = AsyncMock()
        mock.delete_one = AsyncMock()
        yield mock


# =============================================================================
# Resume Parser Mock Fixtures
# =============================================================================


@pytest.fixture
def mock_openai_response():
    """Mock OpenAI API response."""
    mock_response = MagicMock()
    mock_response.content = '{"name": "John Doe", "email": "john@example.com"}'
    return mock_response


@pytest.fixture
def mock_azure_ocr_response():
    """Mock Azure Document Intelligence response."""
    return '{"content": "John Doe\\nSoftware Engineer\\njohn@example.com"}'


@pytest.fixture
def sample_pdf_bytes() -> bytes:
    """Create minimal valid PDF bytes for testing."""
    # Minimal valid PDF structure
    return b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>
endobj
xref
0 4
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
trailer
<< /Size 4 /Root 1 0 R >>
startxref
193
%%EOF"""


# =============================================================================
# Test Data Fixtures
# =============================================================================


@pytest.fixture
def valid_resume_data() -> dict:
    """Return valid resume data for testing."""
    return {
        "personal_information": {
            "name": "John",
            "surname": "Doe",
            "date_of_birth": "1990-01-01",
            "country": "USA",
            "city": "New York",
            "address": "123 Test St",
            "phone_prefix": "+1",
            "phone": "555-0123",
            "email": "john.doe@example.com",
            "github": "github.com/johndoe",
            "linkedin": "linkedin.com/in/johndoe",
        },
        "education_details": [
            {
                "education_level": "Bachelor's",
                "institution": "Test University",
                "field_of_study": "Computer Science",
                "final_evaluation_grade": "3.8",
                "start_date": "2010-09",
                "year_of_completion": "2014",
                "exam": {"course_name": "Final Project", "grade": "A"},
            }
        ],
        "experience_details": [
            {
                "position": "Software Engineer",
                "company": "Tech Corp",
                "employment_period": "2014-2020",
                "location": "New York",
                "industry": "Technology",
                "key_responsibilities": ["Development", "Testing"],
                "skills_acquired": ["Python", "FastAPI"],
            }
        ],
        "projects": [
            {
                "name": "Project X",
                "description": "A test project",
                "link": "github.com/project-x",
            }
        ],
        "achievements": [
            {"name": "Best Developer", "description": "Won best developer award"}
        ],
        "certifications": [
            {"name": "AWS Certified", "description": "AWS Developer Associate"}
        ],
        "languages": [{"language": "English", "proficiency": "Native"}],
        "interests": ["Programming", "Reading"],
        "availability": {"notice_period": "2 weeks"},
        "salary_expectations": {"salary_range_usd": "80000-100000"},
        "self_identification": {
            "gender": "Male",
            "pronouns": "he/him",
            "veteran": "No",
            "disability": "No",
            "ethnicity": "Not specified",
        },
        "legal_authorization": {
            "eu_work_authorization": "Yes",
            "us_work_authorization": "No",
            "requires_us_visa": "No",
            "requires_us_sponsorship": "No",
            "requires_eu_visa": "No",
            "legally_allowed_to_work_in_eu": "Yes",
            "legally_allowed_to_work_in_us": "No",
            "requires_eu_sponsorship": "No",
            "canada_work_authorization": "No",
            "requires_canada_visa": "No",
            "legally_allowed_to_work_in_canada": "No",
            "requires_canada_sponsorship": "No",
            "uk_work_authorization": "No",
            "requires_uk_visa": "No",
            "legally_allowed_to_work_in_uk": "No",
            "requires_uk_sponsorship": "No",
        },
        "work_preferences": {
            "remote_work": "Yes",
            "in_person_work": "No",
            "open_to_relocation": "Yes",
            "willing_to_complete_assessments": "Yes",
            "willing_to_undergo_drug_tests": "Yes",
            "willing_to_undergo_background_checks": "Yes",
        },
    }
