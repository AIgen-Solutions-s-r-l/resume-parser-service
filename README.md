
# Resume Service

## Overview

**Resume Service** is a FastAPI-based microservice designed to handle resume ingestion, retrieval, and updates. It uses MongoDB for storing resumes and integrates with user authentication for secure operations.

### Main Features

- Resume Creation
- Resume Retrieval by User
- Resume Updates

## Setup

### Prerequisites

Ensure you have the following installed!
- Python 3.12.3
- pip
- MongoDB
- Docker (optional, for containerization)
- Tesseract : apt-get install tesseract-ocr tesseract-ocr-eng libtesseract-dev libleptonica-dev pkg-config
              TESSDATA_PREFIX=$(dpkg -L tesseract-ocr-eng | grep tessdata$)
              echo "Set TESSDATA_PREFIX=${TESSDATA_PREFIX}"

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

3. Set up environment variables by renaming `.env.example` to `.env`.

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

### JSON Formatting Guidelines
When constructing JSON payloads for resume creation and updates, adhere to these guidelines:
- **Conditional Field Inclusion**:
  - Atomic fields (non-nested): If empty or unspecified, retain the field and set its value to `null` or `None`.
  - Nested objects/arrays: Include if at least one field/element has data; exclude if entirely empty.
- **Recursion**: Apply these rules recursively.

#### Examples
1. **Empty Atomic Fields**: If personal_information has empty atomic fields, retain them with null values.
   ```json
   {
     "personal_information": {
          "name": "Marco",
          "surname": "Rossi",
          "date_of_birth": "15/08/1995",
          "country": "Italy",
          "city": null,
          "address": null,
          "phone_prefix": "+39",
          "phone": "3401234567",
          "email": "marco.rossi@example.com",
          "github": "https://github.com/marco-rossi/ProjectExample",
          "linkedin": null
        }
   }
   ```

2. **Excluding Empty Nested Objects**: If FOR EXAMPLE the exam object inside education_details is empty but education_details has other fields filled, exclude exam entirely.
   ```json
   {
     "education_details": [
       {
            "education_level": "Master's Degree",
            "institution": "Politecnico di Milano",
            "field_of_study": "Software Engineering",
            "final_evaluation_grade": null,
            "start_date": "2018",
            "year_of_completion": null,
       }
     ]
   }
   ```
Note: In this case, since exam is a nested object and is empty, we exclude it from the JSON entirely.

3. **Including Empty Atomic Fields in Nested Objects & Array with at least one element**:
   ```json
   {
     "experience_details": [
       {
         "position": "Software Engineer",
         "company": "Tech Innovations",
         "employment_period": "06/2020 - Present",
         "location": null,
         "industry": "Technology",
         "key_responsibilities": [
           "Developed scalable web applications"
         ]
       }
     ]
   }
   ```

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

#### 3. `PUT /resumes/update`
- **Description:** Updates an existing resume.
- **Request Example:**
  ```bash
  curl -X PUT "http://localhost:8005/resumes/update" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJqb2huZG9lIiwiaWQiOjQsImlzX2FkbWluIjpmYWxzZSwiZXhwIjoxNzMzMTgzMzI5fQ.Kb3yAeW9PN8eIbttiQmRiOHf9qYDWBuUrkXZwwlNYO8" \
  -d '{
    "education_details": [
      {
        "education_level": "AAAAAAAAA",
        "institution": "VVVVVVVVVV",
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
 
### 4. `POST /resumes/pdf_to_json`
- **Description:** Converts a PDF resume to JSON format using LLMFormat and returns the structured JSON data.
- **Request Example (via `curl`):**
  ```bash
  curl -X POST "http://localhost:8004/resumes/pdf_to_json" \
    -H "accept: application/json" \
    -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
    -F "pdf_file=@resume.pdf"
  ```

- **Responses:**
  - `200 OK`: Resume successfully converted to JSON.
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
            "education_level": "Master's Degree",
            "institution": "Politecnico di Milano",
            "field_of_study": "Software Engineering",
            "final_evaluation_grade": "3.8/4",
            "start_date": "2018",
            "year_of_completion": "2024"
          }
        ],
        "experience_details": [
          {
            "position": "Software Engineer",
            "company": "Tech Innovations",
            "employment_period": "06/2020 - Present",
            "industry": "Technology",
            "key_responsibilities": [
              "Developed scalable web applications"
            ]
          }
        ]
      }
      ```
  - `400 Bad Request`: Invalid resume data or PDF processing error.
    - **Error Example:**
      ```json
      {
        "error": "Failed to generate resume from PDF."
      }
      ```
  - `401 Unauthorized`: Not authenticated.
    - **Error Example:**
      ```json
      {
        "error": "Unauthorized",
        "message": "Authentication required to access this endpoint."
      }
      ```
  - `500 Internal Server Error`: Internal server error occurred during processing.
    - **Error Example:**
      ```json
      {
        "error": "InternalServerError",
        "message": "An error occurred while processing the PDF resume."
      }
      ```

#### 5. `GET /resumes/exists`
- **Description:** Retrieves the authenticated user's resume.
- **Request Example:**
  ```bash
  curl -X GET "http://localhost:8004/resumes/exists"   -H "accept: application/json"   -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
  ```
- **Response Example:**
  ```bash
{
  "exists": true
}
  ```
  
- **Notes:**
  - This endpoint requires an authentication token to verify the current user.
  - The uploaded PDF file should be passed as a `multipart/form-data` field named `pdf_file`.
  - Errors during PDF processing or JSON conversion are logged for debugging purposes.

![Resume 1](https://github.com/user-attachments/assets/222676e1-bd4f-4a20-a556-d844712dd7c4)


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

**Note:** See resume microservice to inspect further details and endpoints

## utils.py full JSON example:
```
{
  "personal_information": {
    "name": "Marco",
    "surname": "Rossi",
    "date_of_birth": "15/08/1995",
    "country": "Italy",
    "city": "Milan",
    "address": "Corso Buenos Aires 12",
    "phone_prefix": "+39",
    "phone": "3401234567",
    "email": "marco.rossi@example.com",
    "github": "https://github.com/marco-rossi/ProjectExample",
    "linkedin": "https://www.linkedin.com/in/marco-rossi"
  },
  "education_details": [
    {
      "education_level": "Master's Degree",
      "institution": "Politecnico di Milano",
      "field_of_study": "Software Engineering",
      "final_evaluation_grade": "3.8/4",
      "start_date": "2018",
      "year_of_completion": "2024",
      "exam": {
        "Data Structures": "3.9",
        "Web Technologies": "3.8",
        "Mobile Development": "4.0",
        "Database Management": "3.7",
        "Machine Learning": "4.0",
        "Cloud Computing": "3.8"
      }
    }
  ],
  "experience_details": [
    {
      "position": "Software Engineer",
      "company": "Tech Innovations",
      "employment_period": "06/2020 - Present",
      "location": "Italy",
      "industry": "Technology",
      "key_responsibilities": [
        "Developed scalable web applications using modern frameworks",
        "Collaborated with cross-functional teams to define project requirements",
        "Implemented RESTful APIs for mobile and web applications",
        "Conducted code reviews and mentored junior developers",
        "Participated in Agile ceremonies and continuous improvement initiatives"
      ],
      "skills_acquired": [
        "JavaScript",
        "React",
        "Node.js",
        "Agile Methodologies",
        "REST APIs",
        "Cloud Services",
        "DevOps Practices",
        "Database Management",
        "Team Collaboration",
        "Technical Documentation"
      ]
    }
  ],
  "projects": [
    {
      "name": "Portfolio Website",
      "description": "Created a personal portfolio website to showcase my projects and skills",
      "link": "https://github.com/marco-rossi/portfolio-website"
    },
    {
      "name": "E-commerce Platform",
      "description": "Developed a full-stack e-commerce application with payment integration and user authentication",
      "link": "https://github.com/marco-rossi/ecommerce-platform"
    }
  ],
  "achievements": [
    {
      "name": "Top Performer",
      "description": "Recognized as a top performer in the software engineering team for three consecutive quarters"
    },
    {
      "name": "Hackathon Winner",
      "description": "Won first place in a regional hackathon for developing an innovative mobile app"
    },
    {
      "name": "Publication",
      "description": "Published an article on Medium about best practices in web development"
    }
  ],
  "certifications": [
    {
      "name": "AWS Certified Solutions Architect",
      "description": "Certification demonstrating proficiency in designing distributed applications and systems on AWS"
    }
  ],
  "languages": [
    {
      "language": "Italian",
      "proficiency": "Native"
    },
    {
      "language": "English",
      "proficiency": "Fluent"
    },
    {
      "language": "Spanish",
      "proficiency": "Intermediate"
    }
  ],
  "interests": [
    "Artificial Intelligence",
    "Blockchain Technology",
    "Open Source Development",
    "Cybersecurity",
    "Game Development",
    "Robotics",
    "Virtual Reality"
  ],
  "availability": {
    "notice_period": "2 weeks"
  },
  "salary_expectations": {
    "salary_range_usd": "80000"
  },
  "self_identification": {
    "gender": "Male",
    "pronouns": "He",
    "veteran": "No",
    "disability": "No",
    "ethnicity": "White"
  },
  "legal_authorization": {
    "eu_work_authorization": "Yes",
    "us_work_authorization": "No",
    "requires_us_visa": "Yes",
    "requires_us_sponsorship": "Yes",
    "requires_eu_visa": "No",
    "legally_allowed_to_work_in_eu": "Yes",
    "legally_allowed_to_work_in_us": "No",
    "requires_eu_sponsorship": "No",
    "canada_work_authorization": "Yes",
    "requires_canada_visa": "Yes",
    "legally_allowed_to_work_in_canada": "Yes",
    "requires_canada_sponsorship": "No",
    "uk_work_authorization": "Yes",
    "requires_uk_visa": "No",
    "legally_allowed_to_work_in_uk": "Yes",
    "requires_uk_sponsorship": "No"
  },
  "work_preferences": {
    "remote_work": "Yes",
    "in_person_work": "Yes",
    "open_to_relocation": "Yes",
    "willing_to_complete_assessments": "Yes",
    "willing_to_undergo_drug_tests": "No",
    "willing_to_undergo_background_checks": "Yes"
  }
}
```
