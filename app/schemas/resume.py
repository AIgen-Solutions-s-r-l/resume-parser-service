from pydantic import BaseModel, EmailStr, AnyUrl, Field, field_serializer
from typing import Optional, List, Dict, Union
from pydantic_core import Url
from langchain.embeddings.openai import OpenAIEmbeddings

class PersonalInformation(BaseModel):
    name: Optional[str]
    surname: Optional[str]
    date_of_birth: Optional[str]
    country: Optional[str]
    city: Optional[str]
    address: Optional[str]
    zip_code: Optional[str] = Field(None, min_length=5, max_length=10)
    phone_prefix: Optional[str]
    phone: Optional[str]
    email: Optional[EmailStr]
    # Allow strings or URLs
    github: Optional[Union[AnyUrl, str]] = None
    linkedin: Optional[Union[AnyUrl, str]] = None

    @field_serializer('github', 'linkedin')
    def url2str(self, val) -> Optional[str]:
        if isinstance(val, Url):
            return str(val)
        return val


class EducationDetails(BaseModel):
    education_level: Optional[str]
    institution: Optional[str]
    field_of_study: Optional[str]
    final_evaluation_grade: Optional[str] = None
    start_date: Optional[str]
    year_of_completion: Optional[Union[int, str]] = None
    exam: Optional[Union[List[Dict[str, str]], Dict[str, str]]] = None


class ExperienceDetails(BaseModel):
    position: Optional[str]
    company: Optional[str]
    employment_period: Optional[str]
    location: Optional[str]
    industry: Optional[str]
    key_responsibilities: Optional[List[str]] = None
    skills_acquired: Optional[List[str]] = None


class Project(BaseModel):
    name: Optional[str]
    description: Optional[str]
    # Allow strings or URLs
    link: Optional[Union[AnyUrl, str]] = None

    @field_serializer('link')
    def url2str(self, val) -> Optional[str]:
        if isinstance(val, Url):
            return str(val)
        return val


class Achievement(BaseModel):
    name: Optional[str]
    description: Optional[str]


class Certification(BaseModel):
    name: Optional[str]
    description: Optional[str]


class Language(BaseModel):
    language: Optional[str]
    proficiency: Optional[str]


class Availability(BaseModel):
    notice_period: Optional[str]


class SalaryExpectations(BaseModel):
    salary_range_usd: Optional[str]


class SelfIdentification(BaseModel):
    gender: Optional[str]
    pronouns: Optional[str]
    veteran: Optional[str]
    disability: Optional[str]
    ethnicity: Optional[str]


class WorkPreferences(BaseModel):
    remote_work: Optional[str]
    in_person_work: Optional[str]
    open_to_relocation: Optional[str]
    willing_to_complete_assessments: Optional[str]
    willing_to_undergo_drug_tests: Optional[str]
    willing_to_undergo_background_checks: Optional[str]


class LegalAuthorization(BaseModel):
    eu_work_authorization: Optional[str]
    us_work_authorization: Optional[str]
    requires_us_visa: Optional[str]
    legally_allowed_to_work_in_us: Optional[str]
    requires_us_sponsorship: Optional[str]
    requires_eu_visa: Optional[str]
    legally_allowed_to_work_in_eu: Optional[str]
    requires_eu_sponsorship: Optional[str]
    canada_work_authorization: Optional[str]
    requires_canada_visa: Optional[str]
    legally_allowed_to_work_in_canada: Optional[str]
    requires_canada_sponsorship: Optional[str]
    uk_work_authorization: Optional[str]
    requires_uk_visa: Optional[str]
    legally_allowed_to_work_in_uk: Optional[str]
    requires_uk_sponsorship: Optional[str]




class ResumeBase(BaseModel):
    education_details: Optional[List[EducationDetails]] = None
    experience_details: Optional[List[ExperienceDetails]] = None
    projects: Optional[List[Project]] = None
    achievements: Optional[List[Achievement]] = None
    certifications: Optional[List[Certification]] = None
    languages: Optional[List[Language]] = None
    interests: Optional[List[str]] = None
    self_identification: Optional[SelfIdentification] = None
    legal_authorization: Optional[LegalAuthorization] = None
    work_preferences: Optional[WorkPreferences] = None
    availability: Optional[Availability] = None
    salary_expectations: Optional[SalaryExpectations] = None


    def to_text(self) -> str:
        """
        Concatenates all relevant fields into a string, with nested fields properly formatted.
        """
        text = ""


        # Education Details
        if self.education_details:
            text += "Education:\n"
            for edu in self.education_details:
                text += f"  - Level: {edu.education_level}, Institution: {edu.institution}, Field of Study: {edu.field_of_study}, "
                text += f"Grade: {edu.final_evaluation_grade}, Start Date: {edu.start_date}, Completion Year: {edu.year_of_completion}\n"
                if edu.exam:
                    text += "    Exams:\n"
                    if isinstance(edu.exam, list):
                        for exam in edu.exam:
                            text += f"      - {exam.get('name', '')}: {exam.get('score', '')}\n"
                    else:
                        text += f"      - {edu.exam.get('name', '')}: {edu.exam.get('score', '')}\n"
        
        # Experience Details
        if self.experience_details:
            text += "Experience:\n"
            for exp in self.experience_details:
                text += f"  - Position: {exp.position}, Company: {exp.company}, Employment Period: {exp.employment_period}, "
                text += f"Location: {exp.location}, Industry: {exp.industry}\n"
                if exp.key_responsibilities:
                    text += "    Key Responsibilities:\n"
                    for responsibility in exp.key_responsibilities:
                        text += f"      - {responsibility}\n"
                if exp.skills_acquired:
                    text += "    Skills Acquired:\n"
                    for skill in exp.skills_acquired:
                        text += f"      - {skill}\n"
        
        # Projects
        if self.projects:
            text += "Projects:\n"
            for project in self.projects:
                text += f"  - Name: {project.name}, Description: {project.description}, Link: {project.link}\n"

        # Achievements
        if self.achievements:
            text += "Achievements:\n"
            for achievement in self.achievements:
                text += f"  - Name: {achievement.name}, Description: {achievement.description}\n"
        
        # Certifications
        if self.certifications:
            text += "Certifications:\n"
            for certification in self.certifications:
                text += f"  - Name: {certification.name}, Description: {certification.description}\n"

        # Languages
        if self.languages:
            text += "Languages:\n"
            for language in self.languages:
                text += f"  - Language: {language.language}, Proficiency: {language.proficiency}\n"

        # Interests
        if self.interests:
            text += "Interests:\n"
            for interest in self.interests:
                text += f"  - {interest}\n"

        # Self Identification
        if self.self_identification:
            text += f"Self Identification:\n"
            text += f"  - Gender: {self.self_identification.gender}, Pronouns: {self.self_identification.pronouns}, "
            text += f"Veteran: {self.self_identification.veteran}, Disability: {self.self_identification.disability}, "
            text += f"Ethnicity: {self.self_identification.ethnicity}\n"

        # Legal Authorization
        if self.legal_authorization:
            text += "Legal Authorization:\n"
            text += f"  - EU Work Authorization: {self.legal_authorization.eu_work_authorization}, "
            text += f"US Work Authorization: {self.legal_authorization.us_work_authorization}, "
            text += f"Requires US Visa: {self.legal_authorization.requires_us_visa}, "
            text += f"Legally Allowed to Work in US: {self.legal_authorization.legally_allowed_to_work_in_us}, "
            text += f"Requires US Sponsorship: {self.legal_authorization.requires_us_sponsorship}, "
            text += f"Requires EU Visa: {self.legal_authorization.requires_eu_visa}, "
            text += f"Legally Allowed to Work in EU: {self.legal_authorization.legally_allowed_to_work_in_eu}, "
            text += f"Requires EU Sponsorship: {self.legal_authorization.requires_eu_sponsorship}, "
            text += f"Canada Work Authorization: {self.legal_authorization.canada_work_authorization}, "
            text += f"Requires Canada Visa: {self.legal_authorization.requires_canada_visa}, "
            text += f"Legally Allowed to Work in Canada: {self.legal_authorization.legally_allowed_to_work_in_canada}, "
            text += f"Requires Canada Sponsorship: {self.legal_authorization.requires_canada_sponsorship}, "
            text += f"UK Work Authorization: {self.legal_authorization.uk_work_authorization}, "
            text += f"Requires UK Visa: {self.legal_authorization.requires_uk_visa}, "
            text += f"Legally Allowed to Work in UK: {self.legal_authorization.legally_allowed_to_work_in_uk}, "
            text += f"Requires UK Sponsorship: {self.legal_authorization.requires_uk_sponsorship}\n"

        # Work Preferences
        if self.work_preferences:
            text += "Work Preferences:\n"
            text += f"  - Remote Work: {self.work_preferences.remote_work}, "
            text += f"In-Person Work: {self.work_preferences.in_person_work}, "
            text += f"Open to Relocation: {self.work_preferences.open_to_relocation}, "
            text += f"Willing to Complete Assessments: {self.work_preferences.willing_to_complete_assessments}, "
            text += f"Willing to Undergo Drug Tests: {self.work_preferences.willing_to_undergo_drug_tests}, "
            text += f"Willing to Undergo Background Checks: {self.work_preferences.willing_to_undergo_background_checks}\n"

        # Availability
        if self.availability:
            text += f"Availability:\n"
            text += f"  - Notice Period: {self.availability.notice_period}\n"

        # Salary Expectations
        if self.salary_expectations:
            text += f"Salary Expectations:\n"
            text += f"  - Salary Range (USD): {self.salary_expectations.salary_range_usd}\n"

        return text        
        
    def model_dump(self, exclude_unset: bool = True) -> dict:
        """
        Overrides the model_dump method to dynamically include the 'vector' field.
        It automatically calculates and returns it as part of the dictionary.
        """
        embeddings = OpenAIEmbeddings(model="text-embedding-ada-002")
        vector = embeddings.embed_query(self.to_text())
        result = super().model_dump(exclude_unset=exclude_unset)
        result['vector'] = vector
        return result
        

class AddResume(ResumeBase):
    user_id: Optional[int] = None
    personal_information: Optional[PersonalInformation]

class AddResume(ResumeBase):
    user_id: Optional[int] = None
    personal_information: Optional[PersonalInformation]


class UpdateResume(ResumeBase):
    user_id: Optional[int] = None
    personal_information: Optional[PersonalInformation] = None

    def model_dump(self, exclude_unset: bool = True) -> dict:
        """
        Esporta i campi modificati, escludendo i campi non impostati.
        """
        return super().model_dump(exclude_unset=exclude_unset)


class PdfJsonResume(ResumeBase):
    personal_information: Optional[PersonalInformation] = None

    def model_dump(self, exclude_unset: bool = True) -> dict:
        """
        Esporta i campi modificati, escludendo i campi non impostati.
        """
        return super().model_dump(exclude_unset=exclude_unset)