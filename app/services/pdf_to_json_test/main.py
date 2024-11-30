import json
from PyPDF2 import PdfReader
from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from gpt_manager import GPTManager

# Main Execution
if __name__ == "__main__":
    openai_api_key = "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"
    pdf_path = "FedericoElia.pdf"  # Path to your PDF file

    manager = GPTManager(openai_api_key)
    pdf_text = manager.pdf_to_text(pdf_path)
    resume_json = manager.pdf_to_plain_text_resume(pdf_text)

    # Save to a JSON file
    with open("resume.json", "w", encoding="utf-8") as f:
        json.dump(resume_json, f, indent=2, ensure_ascii=False)

    print("JSON resume saved to 'resume.json'")
