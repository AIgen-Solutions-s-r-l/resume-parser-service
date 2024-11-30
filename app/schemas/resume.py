from pydantic import BaseModel, EmailStr, AnyUrl, Field, field_serializer
from typing import Optional, List, Dict, Union
from pydantic_core import Url

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
    github: Optional[AnyUrl] = None
    linkedin: Optional[AnyUrl] = None

    @field_serializer('github', 'linkedin')
    def url2str(self, val) -> str:
        if isinstance(val, Url):
            return str(val)
        return val



class EducationDetails(BaseModel):
    education_level: Optional[str]
    institution: Optional[str]
    field_of_study: Optional[str]
    final_evaluation_grade: Optional[str]
    start_date: Optional[str]
    year_of_completion: Optional[Union[int, str]]
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
    link: Optional[AnyUrl] = None

    @field_serializer('link')
    def url2str(self, val) -> str:
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
    user_id: Optional[int] = None
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

class AddResume(ResumeBase):
    personal_information: PersonalInformation

class UpdateResume(ResumeBase):
    personal_information: Optional[PersonalInformation] = None

