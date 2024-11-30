import json
from PyPDF2 import PdfReader
from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

class GPTManager:
    def __init__(self, openai_api_key):
        self.llm = ChatOpenAI(model_name="gpt-4o-mini", openai_api_key=openai_api_key)

    def pdf_to_text(self, pdf_path: str) -> str:
        """Extracts text from a PDF file."""
        reader = PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
        return text

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
        print(response)
        # Parse JSON response
        try:
            resume_json = json.loads(response)
        except json.JSONDecodeError:
            print("Failed to parse JSON. Check the output format.")
            resume_json = {}

        return resume_json
