# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build & Development Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run the service locally (with hot reload)
uvicorn app.main:app --reload

# Run all tests
pytest

# Run tests with coverage
pytest --cov=app --cov-report=term-missing

# Run a specific test file
pytest app/tests/test_main.py

# Run a specific test
pytest app/tests/test_main.py::test_function_name

# Docker build and run
docker build -t resume_service .
docker run -p 8000:8000 --env-file .env resume_service
```

## System Dependencies

Tesseract OCR is required for PDF text extraction:
```bash
apt-get install tesseract-ocr tesseract-ocr-eng libtesseract-dev libleptonica-dev pkg-config
```

## Architecture Overview

This is a FastAPI microservice for resume ingestion, parsing, and management. It processes PDF resumes into structured JSON using a multi-strategy approach combining Azure Document Intelligence and OpenAI Vision.

### Layered Architecture

1. **API Layer** (`app/routers/`) - FastAPI routers with Pydantic validation and JWT auth
2. **Service Layer** (`app/services/`) - Business logic for resume parsing and CRUD operations
3. **Core Layer** (`app/core/`) - MongoDB connection, config, auth, logging, security
4. **Schemas** (`app/schemas/`) - Pydantic data models for request/response validation

### Key Components

- **resume_parser.py** - Orchestrates PDF parsing using Azure OCR + OpenAI vision model
- **resume_service.py** - MongoDB CRUD operations for resumes (user-scoped queries)
- **mongodb.py** - Motor async MongoDB connection management
- **auth.py** / **security.py** - JWT token validation and generation

### Data Flow (PDF to JSON)

1. PDF upload → Router validates file size/format
2. Resume Parser uses dual strategy: Azure Document Intelligence + OpenAI GPT-4o vision
3. LLM repairs/validates JSON output
4. Pydantic schema validation (`schemas/resume.py`)
5. Structured JSON response

### Authentication

All `/resumes/*` endpoints require JWT Bearer token. Token contains `user_id` extracted by `get_current_user` dependency for user-scoped data isolation.

## Key Environment Variables

| Variable | Purpose |
|----------|---------|
| `MONGODB` | MongoDB connection string |
| `MONGODB_DATABASE` | Database name (default: resumes) |
| `SECRET_KEY` | JWT signing secret |
| `OPENAI_API_KEY` | OpenAI API key for GPT-4o |
| `DOCUMENT_INTELLIGENCE_API_KEY` | Azure Document Intelligence key |
| `DOCUMENT_INTELLIGENCE_ENDPOINT` | Azure endpoint URL |
| `LOG_LEVEL` | DEBUG, INFO, WARNING, ERROR, CRITICAL |

## Code Patterns

- **Async-first**: All I/O operations use async/await
- **ThreadPoolExecutor**: Used for CPU-bound OCR operations
- **Dependency Injection**: FastAPI dependencies for auth, config, logging
- **Structured Logging**: Loguru with JSON format and TCP sink to Logstash

## API Endpoints

- `POST /resumes/create_resume` - Create resume
- `GET /resumes/get` - Get user's resume
- `PUT /resumes/update` - Update resume
- `POST /resumes/pdf_to_json` - Convert PDF to JSON
- `GET /resumes/exists` - Check if resume exists
- `GET /healthcheck` - MongoDB health check
