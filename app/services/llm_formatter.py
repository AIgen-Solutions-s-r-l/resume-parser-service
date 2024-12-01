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
        self.llm = ChatOpenAI(model_name="gpt-4o-mini", openai_api_key="YOUR_OPENAI_API_KEY")

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

    def extract_personal_information(self, content: str) -> dict:
        """Extracts personal information from the content."""
        prompt_template = """
        You are an expert in extracting personal information from text resumes.
        Extract the personal information from the following text and provide it in the JSON format:

        {{
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
        }}

        Text content: {content}

        Provide only the JSON output without any additional text.
        """
        prompt = ChatPromptTemplate.from_template(prompt_template)
        chain = prompt | self.llm | StrOutputParser()
        response = chain.invoke({
            "content": content
        })
        try:
            personal_info_json = json.loads(response)
        except json.JSONDecodeError:
            logger.error("Failed to parse personal information JSON.", extra={
                "event_type": "json_parse_error"
            })
            personal_info_json = {}
        return personal_info_json

    def extract_education_details(self, content: str) -> list:
        """Extracts education details from the content."""
        prompt_template = """
        You are an expert in extracting education details from text resumes.
        Extract the education details from the following text and provide it in the JSON format as a list:

        [
            {{
                "degree": "string",
                "field_of_study": "string",
                "institution": "string",
                "start_date": "string",
                "end_date": "string",
                "grade": "string",
                "activities_and_societies": "string",
                "description": "string"
            }},
            ...
        ]

        Text content: {content}

        Provide only the JSON array without any additional text.
        """
        prompt = ChatPromptTemplate.from_template(prompt_template)
        chain = prompt | self.llm | StrOutputParser()
        response = chain.invoke({
            "content": content
        })
        try:
            education_details_json = json.loads(response)
        except json.JSONDecodeError:
            logger.error("Failed to parse education details JSON.", extra={
                "event_type": "json_parse_error"
            })
            education_details_json = []
        return education_details_json

    def extract_experience_details(self, content: str) -> list:
        """Extracts professional experience details from the content."""
        prompt_template = """
        You are an expert in extracting professional experience details from text resumes.
        Extract the experience details from the following text and provide it in the JSON format as a list:

        [
            {{
                "job_title": "string",
                "company": "string",
                "location": "string",
                "start_date": "string",
                "end_date": "string",
                "responsibilities": "string"
            }},
            ...
        ]

        Text content: {content}

        Provide only the JSON array without any additional text.
        """
        prompt = ChatPromptTemplate.from_template(prompt_template)
        chain = prompt | self.llm | StrOutputParser()
        response = chain.invoke({
            "content": content
        })
        try:
            experience_details_json = json.loads(response)
        except json.JSONDecodeError:
            logger.error("Failed to parse experience details JSON.", extra={
                "event_type": "json_parse_error"
            })
            experience_details_json = []
        return experience_details_json

    def extract_projects(self, content: str) -> list:
        """Extracts project details from the content."""
        prompt_template = """
        You are an expert in extracting project details from text resumes.
        Extract the projects from the following text and provide them in the JSON format as a list:

        [
            {{
                "project_name": "string",
                "description": "string",
                "technologies_used": "string",
                "role": "string",
                "start_date": "string",
                "end_date": "string"
            }},
            ...
        ]

        Text content: {content}

        Provide only the JSON array without any additional text.
        """
        prompt = ChatPromptTemplate.from_template(prompt_template)
        chain = prompt | self.llm | StrOutputParser()
        response = chain.invoke({
            "content": content
        })
        try:
            projects_json = json.loads(response)
        except json.JSONDecodeError:
            logger.error("Failed to parse projects JSON.", extra={
                "event_type": "json_parse_error"
            })
            projects_json = []
        return projects_json

    def extract_achievements(self, content: str) -> list:
        """Extracts achievements from the content."""
        prompt_template = """
        You are an expert in extracting achievements from text resumes.
        Extract the achievements from the following text and provide them in the JSON format as a list:

        [
            "string",
            ...
        ]

        Text content: {content}

        Provide only the JSON array without any additional text.
        """
        prompt = ChatPromptTemplate.from_template(prompt_template)
        chain = prompt | self.llm | StrOutputParser()
        response = chain.invoke({
            "content": content
        })
        try:
            achievements_json = json.loads(response)
        except json.JSONDecodeError:
            logger.error("Failed to parse achievements JSON.", extra={
                "event_type": "json_parse_error"
            })
            achievements_json = []
        return achievements_json

    def extract_certifications(self, content: str) -> list:
        """Extracts certifications from the content."""
        prompt_template = """
        You are an expert in extracting certifications from text resumes.
        Extract the certifications from the following text and provide them in the JSON format as a list:

        [
            {{
                "certification_name": "string",
                "issuing_organization": "string",
                "issue_date": "string",
                "expiration_date": "string",
                "credential_id": "string",
                "credential_url": "string"
            }},
            ...
        ]

        Text content: {content}

        Provide only the JSON array without any additional text.
        """
        prompt = ChatPromptTemplate.from_template(prompt_template)
        chain = prompt | self.llm | StrOutputParser()
        response = chain.invoke({
            "content": content
        })
        try:
            certifications_json = json.loads(response)
        except json.JSONDecodeError:
            logger.error("Failed to parse certifications JSON.", extra={
                "event_type": "json_parse_error"
            })
            certifications_json = []
        return certifications_json

    def extract_languages(self, content: str) -> list:
        """Extracts languages and proficiency levels from the content."""
        prompt_template = """
        You are an expert in extracting language proficiencies from text resumes.
        Extract the languages and their proficiency levels from the following text and provide them in the JSON format as a list:

        [
            {{
                "language": "string",
                "proficiency": "string"
            }},
            ...
        ]

        Text content: {content}

        Provide only the JSON array without any additional text.
        """
        prompt = ChatPromptTemplate.from_template(prompt_template)
        chain = prompt | self.llm | StrOutputParser()
        response = chain.invoke({
            "content": content
        })
        try:
            languages_json = json.loads(response)
        except json.JSONDecodeError:
            logger.error("Failed to parse languages JSON.", extra={
                "event_type": "json_parse_error"
            })
            languages_json = []
        return languages_json

    def extract_interests(self, content: str) -> list:
        """Extracts interests from the content."""
        prompt_template = """
        You are an expert in extracting interests from text resumes.
        Extract the interests from the following text and provide them in the JSON format as a list:

        [
            "string",
            ...
        ]

        Text content: {content}

        Provide only the JSON array without any additional text.
        """
        prompt = ChatPromptTemplate.from_template(prompt_template)
        chain = prompt | self.llm | StrOutputParser()
        response = chain.invoke({
            "content": content
        })
        try:
            interests_json = json.loads(response)
        except json.JSONDecodeError:
            logger.error("Failed to parse interests JSON.", extra={
                "event_type": "json_parse_error"
            })
            interests_json = []
        return interests_json

    def extract_availability(self, content: str) -> dict:
        """Extracts availability information from the content."""
        prompt_template = """
        You are an expert in extracting availability information from text resumes.
        Extract the availability from the following text and provide it in the JSON format:

        {{
            "notice_period": "string"
        }}

        Text content: {content}

        Provide only the JSON object without any additional text.
        """
        prompt = ChatPromptTemplate.from_template(prompt_template)
        chain = prompt | self.llm | StrOutputParser()
        response = chain.invoke({
            "content": content
        })
        try:
            availability_json = json.loads(response)
        except json.JSONDecodeError:
            logger.error("Failed to parse availability JSON.", extra={
                "event_type": "json_parse_error"
            })
            availability_json = {}
        return availability_json

    def extract_salary_expectations(self, content: str) -> dict:
        """Extracts salary expectations from the content."""
        prompt_template = """
        You are an expert in extracting salary expectations from text resumes.
        Extract the salary expectations from the following text and provide it in the JSON format:

        {{
            "salary_range_usd": "string"
        }}

        Text content: {content}

        Provide only the JSON object without any additional text.
        """
        prompt = ChatPromptTemplate.from_template(prompt_template)
        chain = prompt | self.llm | StrOutputParser()
        response = chain.invoke({
            "content": content
        })
        try:
            salary_expectations_json = json.loads(response)
        except json.JSONDecodeError:
            logger.error("Failed to parse salary expectations JSON.", extra={
                "event_type": "json_parse_error"
            })
            salary_expectations_json = {}
        return salary_expectations_json

    def extract_self_identification(self, content: str) -> dict:
        """Extracts self-identification information from the content."""
        prompt_template = """
        You are an expert in extracting self-identification information from text resumes.
        Extract the self-identification details from the following text and provide it in the JSON format:

        {{
            "gender": "string",
            "pronouns": "string",
            "veteran": "string",
            "disability": "string",
            "ethnicity": "string"
        }}

        Text content: {content}

        Provide only the JSON object without any additional text.
        """
        prompt = ChatPromptTemplate.from_template(prompt_template)
        chain = prompt | self.llm | StrOutputParser()
        response = chain.invoke({
            "content": content
        })
        try:
            self_identification_json = json.loads(response)
        except json.JSONDecodeError:
            logger.error("Failed to parse self-identification JSON.", extra={
                "event_type": "json_parse_error"
            })
            self_identification_json = {}
        return self_identification_json

    def extract_legal_authorization(self, content: str) -> dict:
        """Extracts legal authorization details from the content."""
        prompt_template = """
        You are an expert in extracting legal authorization details from text resumes.
        Extract the legal authorization details from the following text and provide it in the JSON format:

        {{
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
        }}

        Text content: {content}

        Provide only the JSON object without any additional text.
        """
        prompt = ChatPromptTemplate.from_template(prompt_template)
        chain = prompt | self.llm | StrOutputParser()
        response = chain.invoke({
            "content": content
        })
        try:
            legal_authorization_json = json.loads(response)
        except json.JSONDecodeError:
            logger.error("Failed to parse legal authorization JSON.", extra={
                "event_type": "json_parse_error"
            })
            legal_authorization_json = {}
        return legal_authorization_json

    def extract_work_preferences(self, content: str) -> dict:
        """Extracts work preferences from the content."""
        prompt_template = """
        You are an expert in extracting work preferences from text resumes.
        Extract the work preferences from the following text and provide it in the JSON format:

        {{
            "remote_work": "string",
            "in_person_work": "string",
            "open_to_relocation": "string",
            "willing_to_complete_assessments": "string",
            "willing_to_undergo_drug_tests": "string",
            "willing_to_undergo_background_checks": "string"
        }}

        Text content: {content}

        Provide only the JSON object without any additional text.
        """
        prompt = ChatPromptTemplate.from_template(prompt_template)
        chain = prompt | self.llm | StrOutputParser()
        response = chain.invoke({
            "content": content
        })
        try:
            work_preferences_json = json.loads(response)
        except json.JSONDecodeError:
            logger.error("Failed to parse work preferences JSON.", extra={
                "event_type": "json_parse_error"
            })
            work_preferences_json = {}
        return work_preferences_json

    def generate_resume_from_pdf_bytes(self, pdf_bytes: bytes) -> dict:
        """Given PDF bytes, extracts text and generates a JSON resume."""
        content = self.pdf_to_text(pdf_bytes)
        if not content:
            logger.error("No content extracted from PDF.", extra={
                "event_type": "empty_pdf_content"
            })
            return {}
        resume_json = {}
        resume_json['personal_information'] = self.extract_personal_information(content)
        resume_json['education_details'] = self.extract_education_details(content)
        resume_json['experience_details'] = self.extract_experience_details(content)
        resume_json['projects'] = self.extract_projects(content)
        resume_json['achievements'] = self.extract_achievements(content)
        resume_json['certifications'] = self.extract_certifications(content)
        resume_json['languages'] = self.extract_languages(content)
        resume_json['interests'] = self.extract_interests(content)
        resume_json['availability'] = self.extract_availability(content)
        resume_json['salary_expectations'] = self.extract_salary_expectations(content)
        resume_json['self_identification'] = self.extract_self_identification(content)
        resume_json['legal_authorization'] = self.extract_legal_authorization(content)
        resume_json['work_preferences'] = self.extract_work_preferences(content)
        return resume_json
