# llm_formatter.py

import asyncio
import json
from PyPDF2 import PdfReader
from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
import logging
from io import BytesIO
from fix_busted_json import repair_json
import os
from tempfile import NamedTemporaryFile
from megaparse.core.megaparse import MegaParse
from megaparse.core.parser.unstructured_parser import UnstructuredParser

logger = logging.getLogger(__name__)

def parse_pdf_with_megaparse(self,pdf_path: str) -> dict:
    """
    Parse the PDF using MegaParse and return the JSON response.
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        parser = UnstructuredParser()
        megaparse = MegaParse(parser)

        # Use MegaParse to load the PDF
        response = megaparse.load(pdf_path)
        return response
    finally:
        # Close the event loop
        loop.close()

class LLMFormatter:
    def __init__(self):
        self.llm = ChatOpenAI(model_name="gpt-4o-mini", openai_api_key="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")

    async def pdf_to_text(self, pdf_bytes: bytes) -> str:
        """
        Given PDF bytes, parse and return a JSON resume using MegaParse.
        """
        loop = asyncio.get_event_loop()

        with NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_file:
            tmp_file.write(pdf_bytes)
            tmp_file_path = tmp_file.name

        try:
            response = await loop.run_in_executor(None, lambda: parse_pdf_with_megaparse(tmp_file_path))

            return response

        finally:
            if os.path.exists(tmp_file_path):
                os.remove(tmp_file_path)

    def pdf_to_plain_text_resume(self, content: str) -> dict:
        """Generates a JSON resume from the extracted text."""
        prompt_template = """
            You are an expert in creating structured JSON resumes. Based on the following PDF text, generate a JSON resume that strictly adheres to the provided JSON schema.

            ### RULES:
                - JSON Schema Compliance: Ensure that the output JSON strictly adheres to the provided schema, including all specified field names and nested structures.
                - Field Values: Populate fields with appropriate values extracted from the text. If a field lacks data, explicitly include it in the JSON with a null value.
                - Data Types: Strictly follow the data types defined in the schema (e.g., strings, arrays, objects).
                - No Additional Fields: Do not add any fields not explicitly defined in the schema.
                - Single-Line Output: Provide the JSON as a single-line string without line breaks (\n) or unnecessary whitespace and No Escape Characters. Ensure the output JSON is a VALID json, without any escape characters like backslash.


            ### JSON Schema:
            {{
            "personal_information": {{
                "name": string or null,
                "surname": string or null,
                "date_of_birth": string or null,
                "country": string or null,
                "city": string or null,
                "address": string or null,
                "zip_code": string or null,
                "phone_prefix": string or null,
                "phone": string or null,
                "email": string or null,
                "github": string or null,
                "linkedin": string or null
            }},
            "education_details": [
                {{
                "education_level": string or null,
                "institution": string or null,
                "field_of_study": string or null,
                "final_evaluation_grade": string or null,
                "start_date": string or null,
                "year_of_completion": string or null,
                "exam": {{
                    "Exam name": "Exam grade",
                    "Exam name": "Exam grade",
                    }}
                }}
            ],
            "experience_details": [
                {{
                "position": string or null,
                "company": string or null,
                "employment_period": string or null,
                "location": string or null,
                "industry": string or null,
                "key_responsibilities": [...],
                "skills_acquired": [...]
                }}
            ],
            "projects": [
                {{
                "name": string or null,
                "description": string or null,
                "link": string or null
                }}
            ],
            "achievements": [
                {{
                "name": string or null,
                "description": string or null
                }}
            ],
            "certifications": [
                {{
                "name": string or null,
                "description": string or null
                }}
            ],
            "languages": [
                {{
                "language": string or null,
                "proficiency": string or null
                }}
            ],
            "interests": [...],
            "availability": {{
                "notice_period": string
            }},
            "salary_expectations": {{
                "salary_range_usd": string
            }},
            "self_identification": {{
                "gender": string(Yes or No) or null,
                "pronouns": string(Yes or No) or null,
                "veteran": string(Yes or No) or null,
                "disability": string(Yes or No) or null,
                "ethnicity": string(Yes or No) or null
            }},
            "legal_authorization": {{
                "eu_work_authorization": string(Yes or No) or null,
                "us_work_authorization": string(Yes or No) or null,
                "requires_us_visa": string(Yes or No) or null,
                "legally_allowed_to_work_in_us":string(Yes or No) or null,
                "requires_us_sponsorship": string(Yes or No) or null,
                "requires_eu_visa": string(Yes or No) or null,
                "legally_allowed_to_work_in_eu": string(Yes or No) or null,
                "requires_eu_sponsorship": string(Yes or No) or null,
                "canada_work_authorization": string(Yes or No) or null,
                "requires_canada_visa": string(Yes or No) or null,
                "legally_allowed_to_work_in_canada": string(Yes or No) or null,
                "requires_canada_sponsorship": string(Yes or No) or null,
                "uk_work_authorization": string(Yes or No) or null,
                "requires_uk_visa": string(Yes or No) or null,
                "legally_allowed_to_work_in_uk": string(Yes or No) or null,
                "requires_uk_sponsorship": string(Yes or No) or null
            }},
            "work_preferences": {{
                "remote_work": string(Yes or No) or null,
                "in_person_work": string(Yes or No) or null,
                "open_to_relocation": string(Yes or No) or null,
                "willing_to_complete_assessments": string(Yes or No) or null,
                "willing_to_undergo_drug_tests": string(Yes or No) or null,
                "willing_to_undergo_background_checks": string(Yes or No) or null
            }}


            ### Text Content:
            {content}

            ### Output:
            The results should be provided in json format, Provide only the json code for the resume, without any explanations or additional text and also without ```json ```
        """
        prompt = ChatPromptTemplate.from_template(prompt_template)
        chain = prompt | self.llm | StrOutputParser()

        response = chain.invoke({
            "content": content
        })

        return repair_json(response)

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