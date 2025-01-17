COMBINATION_OCR_PROMPT = """
Instructions:
- **Primary Sources**: Use the EXTERNAL OCR AND LLM OCR as primary sources of information.
- **Translation**: Translate the EXTERNAL OCR into English language BEFORE proceeding with any further processing.
- **Correctness**: You MAY correct any spelling or grammatical errors in the EXTERNAL OCR after translating it in English language.
- **Supplementation**: Fill in any missing or additional details from the LINKS OCR, only when relevant and non-redundant.
- **Contextual Accuracy**: For conflicting information between the two sources (e.g., dates, roles, or responsibilities), choose the most contextually accurate information based on:
    - Consistency with other data points within the OCR outputs.
    - The logical flow of the resume (e.g., career progression, roles, and dates).
- **Projects**: In the projects section, incorporate information from both OCRs, ensuring to include the production titles and links. Include the link URLs as they correspond to the specific productions mentioned.

You MUST:
- Comply strictly with the provided JSON schema in the LLM OCR.
- DO NOT add extra fields not defined in the schema.
- The final output must be a single line of valid JSON, with no backticks, code blocks, or escape characters.
- School Diploma: put ALL school diplomas of any grade and technical certificates in the education_details section.
- Bachelor's, Master's, and Doctorate degrees: put ALL degrees in the education_details section.
- Education and Training: put ALL educations and trainings in the education_details section.
- Scholarships, Awards, Erasmus: put ALL scholarships, awards and Erasmus programs in the achievements section.
- Workshops and Seminars: put ALL workshops or seminars or conference mentioned in the EXTERNAL OCR under the "projects" section.
 
### Final Output:
Only output the final JSON resume. Do not output your markdown transcription or any additional explanations.
Provide only the json code for the resume, without any explanations or additional text and also without ```json ```
"""

BASE_OCR_PROMPT = """
You are tasked with extracting information from the provided text and formatting it as a JSON resume. Accuracy is paramount. Carefully read the text line by line to ensure all data is transcribed correctly.

Follow the instructions carefully.

Extract relevant information from the text with extreme accuracy, reading line by line to avoid errors, and produce a JSON resume strictly following the schema below. You must:
- Carefully read through the entire file content.
- You MUST translate the content into English language.
- Comply strictly with the provided JSON schema.
- If you encounter any unclear formatting in the original content, use your judgment.
- Populate fields with values extracted from the text. If no data is found for a field, set it to null.
- Do not exclude any content from the page.
- DO NOT add extra fields not defined in the schema.
- The final output MUST be a single line of valid JSON, with no backticks, code blocks, or escape characters.
- In the projects section, incorporate any information regarding productions like videos, games, applications, books etc.


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
    "gender": "Male", "Female", "Other" or null,
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

SINGLE_CALL_PROMPT = """
Instructions:
- **Primary Source**: Use the EXTERNAL OCR as the primary source of information.
- **Translation**: Translate the EXTERNAL OCR into English language BEFORE proceeding with any further processing.
- **Correctness**: You MAY correct any spelling or grammatical errors in the EXTERNAL OCR after translating it in English language.
- **Supplementation**: Fill in any missing or additional details from the LINKS OCR, only when relevant and non-redundant.
- **Contextual Accuracy**: For conflicting information between the two sources (e.g., dates, roles, or responsibilities), choose the most contextually accurate information based on:
    - Consistency with other data points within the OCR outputs.
    - The logical flow of the resume (e.g., career progression, roles, and dates).
- **Fields**: For each field in the provided JSON schema, extract the most relevant, longest, and most detailed information available from both OCRs, prioritizing the accuracy of the data over brevity.
- **Projects**: In the projects section, incorporate information from both OCRs, ensuring to include the production titles and links. Include the link URLs as they correspond to the specific productions mentioned.
- **Clear Formatting**: Ensure the final JSON is well-structured, with all fields properly populated, respecting the provided schema format.
                
You MUST:
- DO NOT add extra fields not defined in the schema.
- The final output must be a single line of valid JSON, with no backticks, code blocks, or escape characters.
- School Diploma: put ALL school diplomas of any grade and technical certificates in the education_details section.
- Bachelor's, Master's, and Doctorate degrees: put ALL degrees in the education_details section.
- Education and Training: put ALL educations and trainings in the education_details section.
- Scholarships, Awards, Erasmus: put ALL scholarships, awards and Erasmus programs in the achievements section.
- Workshops and Seminars: put ALL workshops or seminars or conference mentioned in the EXTERNAL OCR under the "projects" section.
 
 
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
    "gender": "Male", "Female", "Other" or null,
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