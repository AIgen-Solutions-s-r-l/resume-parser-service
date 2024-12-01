# llm_formatter.py

import json
from PyPDF2 import PdfReader
from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
import logging
from io import BytesIO

logger = logging.getLogger(__name__)

class LLMFormatter:
    def __init__(self):
        self.llm = ChatOpenAI(model_name="gpt-4o-mini", openai_api_key="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")

    def pdf_to_text(self, pdf_bytes: bytes) -> str:
        """Extracts text from a PDF file given its bytes content."""
        try:
            pdf_file = BytesIO(pdf_bytes)
            reader = PdfReader(pdf_file)
            text = ""
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text
            return text
        except Exception as e:
            logger.error(f"Error reading PDF file: {str(e)}", extra={
                "event_type": "pdf_read_error",
                "error_type": type(e).__name__,
                "error_details": str(e)
            })
            return ""

    def pdf_to_plain_text_resume(self, content: str) -> dict:
        """Generates a JSON resume from the extracted text."""
        prompt_template = """
        You are an expert in creating structured JSON resumes. Based on the following PDF text, generate a JSON resume in the format:

        {{
        "personal_information": {{
            "name": "string",
            "surname": "string",
            "date_of_birth": "string",
            "country": "string",
            "city": "string",
            "address": "string",
            "phone_prefix": "string",
            "phone": "string",
            "email": "string",
            "github": "string",
            "linkedin": "string"
        }},
        "education_details": [...],
        "experience_details": [...],
        "projects": [...],
        "achievements": [...],
        "certifications": [...],
        "languages": [...],
        "interests": [...],
        "availability": {{
            "notice_period": "string"
        }},
        "salary_expectations": {{
            "salary_range_usd": "string"
        }},
        "self_identification": {{
            "gender": "string",
            "pronouns": "string",
            "veteran": "string",
            "disability": "string",
            "ethnicity": "string"
        }},
        "legal_authorization": {{
            "eu_work_authorization": "string",
            "us_work_authorization": "string",
            "requires_us_visa": "string",
            "requires_us_sponsorship": "string",
            "requires_eu_visa": "string",
            "legally_allowed_to_work_in_eu": "string",
            "legally_allowed_to_work_in_us": "string",
            "requires_eu_sponsorship": "string",
            "canada_work_authorization": "string",
            "requires_canada_visa": "string",
            "legally_allowed_to_work_in_canada": "string",
            "requires_canada_sponsorship": "string",
            "uk_work_authorization": "string",
            "requires_uk_visa": "string",
            "legally_allowed_to_work_in_uk": "string",
            "requires_uk_sponsorship": "string"
        }},
        "work_preferences": {{
            "remote_work": "string",
            "in_person_work": "string",
            "open_to_relocation": "string",
            "willing_to_complete_assessments": "string",
            "willing_to_undergo_drug_tests": "string",
            "willing_to_undergo_background_checks": "string"
        }}
        }}

        Text content: {content}
        The results should be provided in json format, Provide only the json code for the resume, without any explanations or additional text and also without ```json ```
        """

        prompt = ChatPromptTemplate.from_template(prompt_template)
        chain = prompt | self.llm | StrOutputParser()

        response = chain.invoke({
            "content": content
        })

        # Parse JSON response
        try:
            resume_json = json.loads(response)
        except json.JSONDecodeError:
            logger.error("Failed to parse JSON. Check the output format.", extra={
                "event_type": "json_parse_error"
            })
            resume_json = {}

        return resume_json

    def generate_resume_from_pdf_bytes(self, pdf_bytes: bytes) -> dict:
        """Given PDF bytes, extracts text and generates a JSON resume."""
        content = self.pdf_to_text(pdf_bytes)
        if not content:
            logger.error("No content extracted from PDF.", extra={
                "event_type": "empty_pdf_content"
            })
            return {}
        resume_json = self.pdf_to_plain_text_resume(content)
        return resume_json
