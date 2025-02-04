# Resume Service

## Overview

**Resume Service** is a FastAPI-based microservice designed to handle resume ingestion, parsing, and management. It leverages MongoDB for data persistence and integrates with Azure services for enhanced text processing capabilities. The service includes robust authentication, text embedding functionality, and comprehensive health monitoring.

### Main Features

- PDF Resume Ingestion and Parsing
- Structured JSON Resume Creation and Management
- Text Embedding Generation
- Secure User Authentication
- Health Monitoring System
- Azure Services Integration

## Project Architecture

### Core Components

- **FastAPI Application**: Main web framework handling HTTP requests
- **MongoDB**: Primary database for resume storage
- **Text Embedder**: Service for generating text embeddings
- **Azure Integration**: Services for enhanced text processing
- **Health Monitoring**: Comprehensive system health checks

### Directory Structure

```
resume_service/
├── app/
│   ├── core/           # Core functionality and configurations
│   ├── libs/           # Utility libraries
│   ├── models/         # Data models
│   ├── routers/        # API endpoints
│   ├── schemas/        # Pydantic schemas
│   ├── services/       # Business logic
│   └── tests/          # Test suite
└── cv_output/         # Output directory for processed resumes
```

## Setup

### Prerequisites

- Python 3.12.3
- MongoDB 6.0+
- pip (latest version)
- Docker (optional, for containerization)
- Tesseract OCR:
  ```bash
  apt-get install tesseract-ocr tesseract-ocr-eng libtesseract-dev libleptonica-dev pkg-config
  TESSDATA_PREFIX=$(dpkg -L tesseract-ocr-eng | grep tessdata$)
  echo "Set TESSDATA_PREFIX=${TESSDATA_PREFIX}"
  ```

### Environment Variables

Create a `.env` file with the following variables:

```env
# Server Configuration
PORT=8000
DEBUG=True
ENVIRONMENT=development

# MongoDB Configuration
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB_NAME=resume_service

# Azure Configuration
AZURE_ENDPOINT=your_azure_endpoint
AZURE_API_KEY=your_azure_api_key

# Security
JWT_SECRET_KEY=your_jwt_secret
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd resume_service
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables by copying `.env.example` to `.env` and updating the values.

4. Run the service:
   ```bash
   uvicorn app.main:app --reload
   ```

### Docker Setup

1. Build the Docker image:
   ```bash
   docker build -t resume_service .
   ```

2. Run the container:
   ```bash
   docker run -p 8000:8000 --env-file .env resume_service
   ```

## Development Guidelines

### Code Style

- Follow PEP 8 guidelines
- Use type hints for all function parameters and return values
- Document all functions and classes using docstrings
- Use async/await for I/O-bound operations

### Testing

Run tests using pytest:
```bash
pytest
```

For coverage report:
```bash
pytest --cov=app --cov-report=term-missing
```

### Logging

Logs are configured in `app/core/logging_config.py`. The service uses structured logging with the following levels:
- DEBUG: Detailed information for debugging
- INFO: General operational information
- WARNING: Warning messages for potential issues
- ERROR: Error messages for actual problems
- CRITICAL: Critical issues requiring immediate attention

## API Documentation

[Previous API documentation content remains unchanged...]

## Troubleshooting

### Common Issues

1. **MongoDB Connection Issues**
   - Verify MongoDB is running: `systemctl status mongodb`
   - Check connection string in `.env`
   - Ensure network connectivity

2. **PDF Processing Errors**
   - Verify Tesseract OCR installation
   - Check PDF file permissions
   - Ensure sufficient system memory

3. **Authentication Issues**
   - Verify JWT secret key configuration
   - Check token expiration settings
   - Ensure proper token format in requests

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

### Pull Request Guidelines

- Include tests for new functionality
- Update documentation as needed
- Follow the existing code style
- Keep changes focused and atomic

## License

[Your License Here]

---

**Note:** Ensure MongoDB is running before starting the application.

For more detailed information about the resume microservice and additional endpoints, please refer to the API documentation.
