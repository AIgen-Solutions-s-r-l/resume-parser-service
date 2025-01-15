BASE_OCR_PROMPT = """
Regarding the following JSON schema, you MUST:
- Comply strictly with the provided JSON schema.
- DO NOT add extra fields not defined in the schema.
- The final output must be a single line of valid JSON, with no backticks, code blocks, or escape characters.

### JSON SCHEMA:
{
"personal_information": {
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
},
"education_details": [
    {
    "education_level": string or null,
    "institution": string or null,
    "field_of_study": string or null,
    "final_evaluation_grade": string or null,
    "start_date": string or null,
    "year_of_completion": string or null,
    "exam": {
        "Exam name": "Exam grade",
        "Exam name": "Exam grade"
        }
    }
],
"experience_details": [
    {
    "position": string or null,
    "company": string or null,
    "employment_period": string or null,
    "location": string or null,
    "industry": string or null,
    "key_responsibilities": [...],
    "skills_acquired": [...],
    "links": [
        "link1",
        "link2"
    ]
    }
],
"projects": [
    {
    "name": string or null,
    "description": string or null,
    "link": string or null
    }
],
"achievements": [
    {
    "name": string or null,
    "description": string or null
    }
],
"certifications": [
    {
    "name": string or null,
    "description": string or null
    }
],
"languages": [
    {
    "language": string or null,
    "proficiency": string or null
    }
],
"interests": [...],
"availability": {
    "notice_period": string or null
},
"salary_expectations": {
    "salary_range_usd": string(number) or null
},
"self_identification": {
    "gender": "Yes", "No" or null,
    "pronouns": "Yes", "No" or null or null,
    "veteran": "Yes", "No" or null,
    "disability": "Yes", "No" or null,
    "ethnicity": "Yes", "No" or null
    "hispanic_or_latino": "Yes", "No" or null,
},
"legal_authorization": {
    "eu_work_authorization": "Yes", "No" or null,
    "us_work_authorization": "Yes", "No" or null,
    "requires_us_visa": "Yes", "No" or null,
    "legally_allowed_to_work_in_us":"Yes", "No" or null,
    "requires_us_sponsorship": "Yes", "No" or null,
    "requires_eu_visa": "Yes", "No" or null,
    "legally_allowed_to_work_in_eu": "Yes", "No" or null,
    "requires_eu_sponsorship": "Yes", "No" or null,
    "canada_work_authorization": "Yes", "No" or null,
    "requires_canada_visa": "Yes", "No" or null,
    "legally_allowed_to_work_in_canada": "Yes", "No" or null,
    "requires_canada_sponsorship": "Yes", "No" or null,
    "uk_work_authorization": "Yes", "No" or null,
    "requires_uk_visa": "Yes", "No" or null,
    "legally_allowed_to_work_in_uk": "Yes", "No" or null,
    "requires_uk_sponsorship": "Yes", "No" or null
},
"work_preferences": {
    "remote_work": "Yes", "No" or null,
    "in_person_work": "Yes", "No" or null,
    "open_to_relocation": "Yes", "No" or null,
    "willing_to_complete_assessments": "Yes", "No" or null,
    "willing_to_undergo_drug_tests": "Yes", "No" or null,
    "willing_to_undergo_background_checks": "Yes", "No" or null
}
}

### Final Output:
Only output the final JSON resume. Do not output your markdown transcription or any additional explanations.
Provide only the json code for the resume, without any explanations or additional text and also without ```json ```
"""
