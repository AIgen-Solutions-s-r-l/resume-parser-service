
# Resume Service

## Overview

**Resume Service** is a FastAPI-based microservice designed to handle resume ingestion, retrieval, and updates. It uses MongoDB for storing resumes and integrates with user authentication for secure operations.

### Main Features

- Resume Creation
- Resume Retrieval by User
- Resume Updates

## Setup

### Prerequisites

Ensure you have the following installed:
- Python 3.12.3
- pip
- MongoDB
- Docker (optional, for containerization)

### Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd resume_service-main
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables in a `.env` file:
   ```env
   MONGODB=mongodb://localhost:27017
   RABBITMQ_URL=amqp://guest:guest@localhost:5672/
   ```

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

## API Documentation

### Endpoints

#### 1. `POST /resumes/create_resume`
- **Description:** Creates a new resume in the database.
- **Request Example:**
  ```bash
  curl -X POST "http://localhost:8005/resumes/create_resume"   -H "accept: application/json"   -H "Content-Type: application/json"   -H "Authorization: Bearer YOUR_ACCESS_TOKEN"   -d '{
    "personal_information": {
      "name": "Marco",
      "surname": "Rossi",
      "date_of_birth": "1995-08-15",
      "email": "marco.rossi@example.com"
    },
    "education_details": [
      {
        "education_level": "Masters Degree",
        "institution": "Politecnico di Milano",
        "field_of_study": "Software Engineering",
        "final_evaluation_grade": "3.8/4",
        "start_date": "2018",
        "year_of_completion": "2024"
      }
    ]
  }'
  ```
- **Responses:**
  - `201 Created`: Resume successfully created.
  - `400 Bad Request`: Invalid data provided.
  - `404 Not Found`: User not found.
  - `500 Internal Server Error`: Server error.

---

#### 2. `GET /resumes/get`
- **Description:** Retrieves the authenticated user's resume.
- **Request Example:**
  ```bash
  curl -X GET "http://localhost:8004/resumes/get"   -H "accept: application/json"   -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
  ```
- **Response Example:**
  ```json
  {
    "personal_information": {
      "name": "Marco",
      "surname": "Rossi",
      "email": "marco.rossi@example.com"
    },
    "education_details": [
      {
        "education_level": "Masters Degree",
        "institution": "Politecnico di Milano",
        "field_of_study": "Software Engineering",
        "final_evaluation_grade": "3.8/4",
        "start_date": "2018",
        "year_of_completion": "2024"
      }
    ]
  }
  ```
- **Responses:**
  - `200 OK`: Resume retrieved successfully.
  - `401 Unauthorized`: Not authenticated.
  - `403 Forbidden`: Not authorized to access this resume.
  - `404 Not Found`: Resume not found.
  - `500 Internal Server Error`: Server error.

---

#### 3. `POST /resumes/update`
- **Description:** Updates an existing resume.
- **Request Example:**
  ```bash
  curl -X POST "http://localhost:8004/resumes/update"   -H "accept: application/json"   -H "Content-Type: application/json"   -H "Authorization: Bearer YOUR_ACCESS_TOKEN"   -d '{
    "education_details": [
      {
        "education_level": "MiddleSchool",
        "institution": "Unknown",
        "field_of_study": "Life",
        "final_evaluation_grade": "3.8/4",
        "start_date": "2018",
        "year_of_completion": "2024"
      }
    ]
  }'
  ```
- **Responses:**
  - `200 OK`: Resume successfully updated.
  - `400 Bad Request`: Invalid data provided.
  - `404 Not Found`: Resume not found.
  - `500 Internal Server Error`: Server error.

## Testing

Run tests using:
```bash
pytest
```

## Logging

Logs are configured using `app/core/logging_config.py`.

## Contributing

Contributions are welcome! Please create an issue or submit a pull request.

---

**Note:** Ensure all required services (MongoDB, RabbitMQ) are running before starting the application.
