# Resume Parser Service

A FastAPI microservice for resume ingestion, parsing, and management. Converts PDF resumes to structured JSON using Azure Document Intelligence and OpenAI GPT-4 Vision.

## Features

- **PDF to JSON Conversion**: Parse PDF resumes into structured JSON format
- **Dual OCR Strategy**: Azure Document Intelligence + OpenAI GPT-4o Vision
- **Smart Combination**: LLM-powered merging of OCR results for accuracy
- **Link Extraction**: Automatic extraction of URLs from PDF documents
- **JWT Authentication**: Secure API access with token-based auth
- **MongoDB Storage**: Persistent resume data storage
- **Health Monitoring**: Kubernetes-ready health endpoints

## Quick Start

### Using Docker Compose (Recommended)

```bash
# Clone the repository
git clone https://github.com/AIgen-Solutions-s-r-l/resume-parser-service.git
cd resume-parser-service

# Copy environment file
cp .env.example .env
# Edit .env with your API keys

# Start services
docker-compose up -d

# View logs
docker-compose logs -f app
```

The API will be available at `http://localhost:8000`.

### Manual Installation

```bash
# Prerequisites: Python 3.12+, MongoDB 7.0+, Tesseract OCR

# Install system dependencies (Ubuntu/Debian)
sudo apt-get install tesseract-ocr tesseract-ocr-eng poppler-utils

# Install Python dependencies
pip install poetry
poetry install

# Run the service
uvicorn app.main:app --reload
```

## API Endpoints

### Resume Operations

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/resumes/pdf_to_json` | Convert PDF to JSON resume |
| `POST` | `/resumes/create_resume` | Create a new resume |
| `GET` | `/resumes/get` | Get current user's resume |
| `PUT` | `/resumes/update` | Update existing resume |
| `GET` | `/resumes/exists` | Check if user has a resume |

### Health Checks

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/healthcheck` | Full health check with dependencies |
| `GET` | `/health` | Alias for /healthcheck |
| `GET` | `/ready` | Kubernetes readiness probe |
| `GET` | `/live` | Kubernetes liveness probe |

### Authentication

All `/resumes/*` endpoints require JWT Bearer token authentication.

```bash
curl -X GET "http://localhost:8000/resumes/get" \
  -H "Authorization: Bearer <your-jwt-token>"
```

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         FastAPI Application                      │
├─────────────────────────────────────────────────────────────────┤
│  Routers          │  Services           │  Core                  │
│  ├─ resume        │  ├─ resume_parser   │  ├─ config            │
│  └─ healthcheck   │  └─ resume_service  │  ├─ auth              │
│                   │                     │  ├─ dependencies      │
│  Repositories     │  External Services  │  ├─ middleware        │
│  └─ resume_repo   │  ├─ Azure Doc AI    │  └─ healthcheck       │
│                   │  └─ OpenAI GPT-4o   │                        │
├─────────────────────────────────────────────────────────────────┤
│                         MongoDB                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Directory Structure

```
resume_service/
├── app/
│   ├── core/           # Configuration, auth, middleware, DI
│   ├── repositories/   # Data access layer (Repository pattern)
│   ├── routers/        # API endpoints
│   ├── schemas/        # Pydantic models
│   ├── services/       # Business logic
│   └── tests/          # Test suite
├── .github/workflows/  # CI/CD pipelines
├── docker-compose.yml  # Local development setup
└── Dockerfile          # Production container
```

### PDF Processing Flow

```
PDF Upload → Validate → Azure OCR ─┐
                      → GPT-4 OCR ──┼→ LLM Combine → JSON Repair → Response
                      → Link Extract┘
```

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `MONGODB` | MongoDB connection string | Yes |
| `MONGODB_DATABASE` | Database name (default: resumes) | No |
| `SECRET_KEY` | JWT signing secret (min 32 chars) | Yes |
| `OPENAI_API_KEY` | OpenAI API key for GPT-4o | Yes |
| `DOCUMENT_INTELLIGENCE_API_KEY` | Azure Document Intelligence key | Yes |
| `DOCUMENT_INTELLIGENCE_ENDPOINT` | Azure endpoint URL | Yes |
| `CORS_ORIGINS` | Allowed CORS origins (comma-separated) | No |
| `LOG_LEVEL` | Logging level (DEBUG, INFO, WARNING, ERROR) | No |
| `ENVIRONMENT` | Environment name (development, production) | No |

### Example `.env` file

```env
# Database
MONGODB=mongodb://localhost:27017
MONGODB_DATABASE=resumes

# Security
SECRET_KEY=your-super-secret-key-minimum-32-characters

# External Services
OPENAI_API_KEY=sk-...
DOCUMENT_INTELLIGENCE_API_KEY=your-azure-key
DOCUMENT_INTELLIGENCE_ENDPOINT=https://your-resource.cognitiveservices.azure.com

# Optional
CORS_ORIGINS=http://localhost:3000,http://localhost:8080
LOG_LEVEL=INFO
ENVIRONMENT=development
```

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=term-missing

# Run specific test file
pytest app/tests/test_resume_parser.py -v
```

### Code Quality

```bash
# Format code
black app/
isort app/

# Lint
flake8 app/

# Type check
mypy app/

# Security scan
bandit -r app/ -x app/tests/
```

### Pre-commit Hooks

```bash
# Install pre-commit hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

## Deployment

### Docker

```bash
# Build production image
docker build -t resume-parser-service:latest .

# Run container
docker run -p 8000:8000 --env-file .env resume-parser-service:latest
```

### Docker Compose (with MongoDB)

```bash
# Production
docker-compose -f docker-compose.yml up -d

# Development with hot reload
docker-compose up -d

# With MongoDB admin UI
docker-compose --profile tools up -d
```

### Kubernetes

The service includes Kubernetes-ready health endpoints:
- `/live` - Liveness probe (is the process running?)
- `/ready` - Readiness probe (is the service ready to accept traffic?)

## Troubleshooting

### Common Issues

**MongoDB Connection Failed**
```bash
# Check MongoDB is running
docker-compose ps mongodb

# Check connection string
echo $MONGODB
```

**PDF Processing Errors**
```bash
# Verify Tesseract installation
tesseract --version

# Check poppler installation
pdftoppm -v
```

**Authentication Errors**
- Ensure `SECRET_KEY` is at least 32 characters
- Check token expiration (default: 30 minutes)
- Verify token format: `Bearer <token>`

## License

MIT License - see [LICENSE](LICENSE) for details.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines.
