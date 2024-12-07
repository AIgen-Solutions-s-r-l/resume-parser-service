BASE_OCR_PROMPT = """
You are tasked with transcribing and formatting the content of a file into markdown (Step 1) and then producing a JSON resume (Step 2) from that structured understanding.

Follow the instructions carefully.

### STEP 1: Transcription to Markdown (Internal Representation Only)
- Carefully read through the entire file content.
- Transcribe the content into markdown format, paying close attention to the existing formatting and structure.
- If you encounter any unclear formatting in the original content, use your judgment to add appropriate markdown formatting to improve readability and structure.
- For tables, headers, and table of contents, add the following tags:
   - Tables: Enclose the entire table in [TABLE] and [/TABLE] tags. Merge the content of tables if it continues on the next page.
   - Headers (complete chain of characters repeated at the start of each page): Enclose in [HEADER] and [/HEADER] tags.
   - Table of contents: Enclose in [TOC] and [/TOC] tags.
- When transcribing tables:
   - If a table continues across multiple pages, merge the content into a single, cohesive table.
   - Use proper markdown table formatting with pipes (|) and hyphens (-) for the table structure.
- Do not include page breaks in your transcription.
- Maintain the logical flow and structure of the document, ensuring that sections and subsections are properly formatted using markdown headers (#, ##, etc.).
- Use appropriate markdown syntax for other formatting elements such as bold, italic, lists, and code blocks as needed.
- After completing this step, you will have an internal well-structured markdown representation of the document (this is for your own reasoning). Do NOT return this markdown as your final answer.

### STEP 2: Generate Final JSON Resume
Now, using your internal structured markdown understanding from Step 1 (do not output the markdown), produce a JSON resume strictly following the schema below. You must:
- Comply strictly with the provided JSON schema.
- Populate fields with values extracted from the text. If no data for a field, set it to null.
- Do not add extra fields not defined in the schema.
- Make sure the final output is a single line of valid JSON, with no backticks, code blocks, or escape characters.

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
    "skills_acquired": [...]
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
    "notice_period": string
},
"salary_expectations": {
    "salary_range_usd": string
},
"self_identification": {
    "gender": string(Yes or No) or null,
    "pronouns": string(Yes or No) or null,
    "veteran": string(Yes or No) or null,
    "disability": string(Yes or No) or null,
    "ethnicity": string(Yes or No) or null
},
"legal_authorization": {
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
},
"work_preferences": {
    "remote_work": string(Yes or No) or null,
    "in_person_work": string(Yes or No) or null,
    "open_to_relocation": string(Yes or No) or null,
    "willing_to_complete_assessments": string(Yes or No) or null,
    "willing_to_undergo_drug_tests": string(Yes or No) or null,
    "willing_to_undergo_background_checks": string(Yes or No) or null
}
}

### Final Output:
Only output the final JSON resume. Do not output your markdown transcription or any additional explanations.
Provide only the json code for the resume, without any explanations or additional text and also without ```json ```
"""