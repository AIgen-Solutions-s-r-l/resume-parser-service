from pydantic import BaseModel, EmailStr, AnyUrl, Field, field_serializer
from typing import Optional, List, Dict, Union
from pydantic_core import Url


class PersonalInformation(BaseModel):
    name: Optional[str] = None
    surname: Optional[str] = None
    date_of_birth: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None
    address: Optional[str] = None
    zip_code: Optional[str] = Field(None, max_length=10)
    phone_prefix: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    github: Optional[Union[AnyUrl, str]] = None
    linkedin: Optional[Union[AnyUrl, str]] = None

    @field_serializer('github', 'linkedin')
    def url2str(self, val) -> Optional[str]:
        if isinstance(val, Url):
            return str(val)
        return val


class RelevantModule(BaseModel):
    module: Optional[str] = None
    grade: Optional[str] = None


class ExamDetails(BaseModel):
    relevant_modules: Optional[List[RelevantModule]] = None


class EducationDetails(BaseModel):
    education_level: Optional[str] = None
    institution: Optional[str] = None
    field_of_study: Optional[str] = None
    final_evaluation_grade: Optional[str] = None
    start_date: Optional[str] = None
    year_of_completion: Optional[Union[int, str]] = None
    exam: Optional[Union[List[Dict[str, str]],
                         Dict[str, str], ExamDetails]] = None


class ExperienceDetails(BaseModel):
    position: Optional[str] = None
    company: Optional[str] = None
    employment_period: Optional[str] = None
    location: Optional[str] = None
    industry: Optional[str] = None
    key_responsibilities: Optional[List[str]] = None
    skills_acquired: Optional[List[str]] = None


class Project(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    link: Optional[Union[AnyUrl, str]] = None

    @field_serializer('link')
    def url2str(self, val) -> Optional[str]:
        if isinstance(val, Url):
            return str(val)
        return val


class Achievement(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class Certification(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class Language(BaseModel):
    language: Optional[str] = None
    proficiency: Optional[str] = None


class Availability(BaseModel):
    notice_period: Optional[str] = None


class SalaryExpectations(BaseModel):
    salary_range_usd: Optional[str] = None


class SelfIdentification(BaseModel):
    gender: Optional[str] = None
    pronouns: Optional[str] = None
    veteran: Optional[str] = None
    disability: Optional[str] = None
    ethnicity: Optional[str] = None


class WorkPreferences(BaseModel):
    remote_work: Optional[str] = None
    in_person_work: Optional[str] = None
    open_to_relocation: Optional[str] = None
    willing_to_complete_assessments: Optional[str] = None
    willing_to_undergo_drug_tests: Optional[str] = None
    willing_to_undergo_background_checks: Optional[str] = None


class LegalAuthorization(BaseModel):
    eu_work_authorization: Optional[str] = None
    us_work_authorization: Optional[str] = None
    requires_us_visa: Optional[str] = None
    legally_allowed_to_work_in_us: Optional[str] = None
    requires_us_sponsorship: Optional[str] = None
    requires_eu_visa: Optional[str] = None
    legally_allowed_to_work_in_eu: Optional[str] = None
    requires_eu_sponsorship: Optional[str] = None
    canada_work_authorization: Optional[str] = None
    requires_canada_visa: Optional[str] = None
    legally_allowed_to_work_in_canada: Optional[str] = None
    requires_canada_sponsorship: Optional[str] = None
    uk_work_authorization: Optional[str] = None
    requires_uk_visa: Optional[str] = None
    legally_allowed_to_work_in_uk: Optional[str] = None
    requires_uk_sponsorship: Optional[str] = None


class ResumeBase(BaseModel):
    personal_information: Optional[PersonalInformation] = None
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
    vector: Optional[List[float]] = None
    
    def to_text(self) -> str:
        text_parts = []
        
        if hasattr(self, 'personal_information') and self.personal_information:
            pi = self.personal_information
            pi_parts = []
            if pi.name:
                pi_parts.append(f"Name: {pi.name}")
            if pi.surname:
                pi_parts.append(f"Surname: {pi.surname}")
            if pi.country:
                pi_parts.append(f"Country: {pi.country}")
            if pi.city:
                pi_parts.append(f"City: {pi.city}")
            if pi_parts:
                text_parts.append("Personal Information:\n" + "\n".join(pi_parts))

        # Education details
        if self.education_details:
            edu_sections = []
            for edu in self.education_details:
                edu_parts = []
                if edu.education_level:
                    edu_parts.append(f"Level: {edu.education_level}")
                if edu.institution:
                    edu_parts.append(f"Institution: {edu.institution}")
                if edu.field_of_study:
                    edu_parts.append(f"Field: {edu.field_of_study}")
                if edu.final_evaluation_grade:
                    edu_parts.append(f"Grade: {edu.final_evaluation_grade}")
                if edu.start_date:
                    edu_parts.append(f"Started: {edu.start_date}")
                if edu.year_of_completion:
                    edu_parts.append(f"Completed: {edu.year_of_completion}")
                if edu_parts:
                    edu_sections.append("\n".join(edu_parts))
            if edu_sections:
                text_parts.append("Education:\n" + "\n\n".join(edu_sections))

        # Experience details
        if self.experience_details:
            exp_sections = []
            for exp in self.experience_details:
                exp_parts = []
                if exp.position:
                    exp_parts.append(f"Position: {exp.position}")
                if exp.company:
                    exp_parts.append(f"Company: {exp.company}")
                if exp.employment_period:
                    exp_parts.append(f"Period: {exp.employment_period}")
                if exp.location:
                    exp_parts.append(f"Location: {exp.location}")
                if exp.industry:
                    exp_parts.append(f"Industry: {exp.industry}")
                if exp.key_responsibilities:
                    exp_parts.append("Key Responsibilities:\n- " + "\n- ".join(exp.key_responsibilities))
                if exp.skills_acquired:
                    exp_parts.append("Skills Acquired:\n- " + "\n- ".join(exp.skills_acquired))
                if exp_parts:
                    exp_sections.append("\n".join(exp_parts))
            if exp_sections:
                text_parts.append("Experience:\n" + "\n\n".join(exp_sections))

        # Projects
        if self.projects:
            proj_sections = []
            for proj in self.projects:
                proj_parts = []
                if proj.name:
                    proj_parts.append(f"Name: {proj.name}")
                if proj.description:
                    proj_parts.append(f"Description: {proj.description}")
                if proj.link:
                    proj_parts.append(f"Link: {proj.link}")
                if proj_parts:
                    proj_sections.append("\n".join(proj_parts))
            if proj_sections:
                text_parts.append("Projects:\n" + "\n\n".join(proj_sections))

        # Achievements
        if self.achievements:
            ach_sections = []
            for ach in self.achievements:
                ach_parts = []
                if ach.name:
                    ach_parts.append(f"Name: {ach.name}")
                if ach.description:
                    ach_parts.append(f"Description: {ach.description}")
                if ach_parts:
                    ach_sections.append("\n".join(ach_parts))
            if ach_sections:
                text_parts.append("Achievements:\n" + "\n\n".join(ach_sections))

        # Certifications
        if self.certifications:
            cert_sections = []
            for cert in self.certifications:
                cert_parts = []
                if cert.name:
                    cert_parts.append(f"Name: {cert.name}")
                if cert.description:
                    cert_parts.append(f"Description: {cert.description}")
                if cert_parts:
                    cert_sections.append("\n".join(cert_parts))
            if cert_sections:
                text_parts.append("Certifications:\n" + "\n\n".join(cert_sections))

        # Languages
        if self.languages:
            lang_parts = []
            for lang in self.languages:
                if lang.language and lang.proficiency:
                    lang_parts.append(f"{lang.language}: {lang.proficiency}")
            if lang_parts:
                text_parts.append("Languages:\n" + "\n".join(lang_parts))

        # Interests
        if self.interests:
            text_parts.append("Interests:\n- " + "\n- ".join(self.interests))

        # Work Preferences
        if self.work_preferences:
            wp = self.work_preferences
            wp_parts = []
            if wp.remote_work:
                wp_parts.append(f"Remote Work: {wp.remote_work}")
            if wp.in_person_work:
                wp_parts.append(f"In-Person Work: {wp.in_person_work}")
            if wp.open_to_relocation:
                wp_parts.append(f"Open to Relocation: {wp.open_to_relocation}")
            if wp_parts:
                text_parts.append("Work Preferences:\n" + "\n".join(wp_parts))

        # Legal Authorization
        if self.legal_authorization:
            la = self.legal_authorization
            la_parts = []
            if la.us_work_authorization:
                la_parts.append(f"US Work Authorization: {la.us_work_authorization}")
            if la.eu_work_authorization:
                la_parts.append(f"EU Work Authorization: {la.eu_work_authorization}")
            if la.uk_work_authorization:
                la_parts.append(f"UK Work Authorization: {la.uk_work_authorization}")
            if la.canada_work_authorization:
                la_parts.append(f"Canada Work Authorization: {la.canada_work_authorization}")
            if la_parts:
                text_parts.append("Legal Authorization:\n" + "\n".join(la_parts))

        return "\n\n".join(text_parts)

    def model_dump(self, exclude_unset: bool = True) -> dict:
        from app.libs.text_embedder import TextEmbedder
        text_embedder = TextEmbedder()
        # get_embeddings returns List[List[float]], we want the first embedding
        embeddings = text_embedder.get_embeddings(self.to_text())
        self.vector = embeddings[0] if embeddings else None
        return super().model_dump(exclude_unset=exclude_unset)