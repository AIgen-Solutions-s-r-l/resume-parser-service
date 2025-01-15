import os
import fitz
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Any
from tempfile import NamedTemporaryFile
from fix_busted_json import repair_json
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from app.services.prompt import BASE_OCR_PROMPT
from app.services.read_azure import analyze_read


logger = logging.getLogger(__name__)

class ResumeParser:
    """
    A single class that handles:
    - External OCR service
    - JSON extraction and repair
    - Combining results from both approaches via another LLM call
    """

    def __init__(self, model_name: str = "gpt-4o-mini", openai_api_key: str = None, executor: ThreadPoolExecutor = None):
        """
        :param model_name: Name of the model with vision + text capabilities.
        :param openai_api_key: Your OpenAI API key.
        """
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        if not self.openai_api_key:
            raise ValueError("OpenAI API key not provided.")

        # Initialize the ChatOpenAI client
        self.model_name = model_name
        self.llm = ChatOpenAI(
            model_name=self.model_name,
            openai_api_key=self.openai_api_key
        )

        self._executor: ThreadPoolExecutor | None = None
    
    def set_executor(self, executor: ThreadPoolExecutor):
        """Inject the shared ThreadPoolExecutor after initialization."""
        self._executor = executor
        
    def extract_links_from_pdf(self, pdf_file_path):
        doc = fitz.open(pdf_file_path)
        urls = []
                
        # Iterate over each page in the PDF
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)  # Get the page
            
            # Extract links from the page (links can be represented as actions)
            links = page.get_links()
            
            for link in links:
                if 'uri' in link:
                    uri = link['uri']
                    if uri:
                        urls.append(uri)
        return urls
    
    async def _combine_ocr_results(self, external_ocr: str, links: str) -> str:
        """
        Combine the results from the external OCR and extracted links into a single JSON resume.
        """
        combination_prompt = f"""
            You are provided with two OCR outputs from the same resume:
            1. **EXTERNAL OCR**: {external_ocr}
            2. **LINKS OCR**: {links}

            Instructions:
            - **Primary Source**: Use the EXTERNAL OCR as the primary source of information.
            - **Supplementation**: Fill in any missing or additional details from the LINKS OCR, only when relevant and non-redundant.
            - **Contextual Accuracy**: For conflicting information between the two sources (e.g., dates, roles, or responsibilities), choose the most contextually accurate information based on:
                - Consistency with other data points within the OCR outputs.
                - The logical flow of the resume (e.g., career progression, roles, and dates).
            - **No Invention**: Do not create or infer any missing information. If a field is absent from both OCRs, leave it as null.
            - **Fields**: For each field in the provided JSON schema, extract the most relevant, longest, and most detailed information available from both OCRs, prioritizing the accuracy of the data over brevity.
            - **Projects**: In the "projects" section, incorporate information from both OCRs, ensuring to include the production titles and links, even if they appear only in the LINKS OCR. Include the link URLs as they correspond to the specific productions mentioned.
            - **Clear Formatting**: Ensure the final JSON is well-structured, with all fields properly populated, respecting the provided schema format.
            
            {BASE_OCR_PROMPT}
        """
        
        message = HumanMessage(content=combination_prompt)
        response = await self.llm.ainvoke([message])
        return response.content

    async def _parse_pdf_bytes_async(self, pdf_bytes: bytes) -> Dict[str, Any]:
        """
        Given PDF bytes, writes them to a temporary file and:
        1. Gets the external OCR result (Azure).
        2. Extracts links from the PDF.
        3. Combines both results via another LLM call.
        """
        with NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_file:
            tmp_file.write(pdf_bytes)
            tmp_file_path = tmp_file.name
        
        try:
            # Step 1: Run external OCR
            external_ocr = await analyze_read(tmp_file_path)
            
            # Warns for empty results
            if not external_ocr.strip():
                logger.warning("External OCR returned empty or invalid content.")

            # Step 2: Extract links from the PDF
            links = self.extract_links_from_pdf(tmp_file_path)

            # Step 3: Combine both results via another LLM call
            combined_response = await self._combine_ocr_results(external_ocr, links)
            
            # Attempt to repair the final combined JSON
            try:
                final_json = repair_json(combined_response)
                return final_json
            except Exception as e:
                logger.error("Failed to parse the combined JSON.", extra={"error": str(e)})
                return {"error": "Failed to parse the combined JSON."}

        except Exception as e:
            logger.error("Failed to parse PDF bytes using both methods.", extra={"error": str(e)})
            return {"error": "Failed to process PDF."}
        finally:
            if os.path.exists(tmp_file_path):
                os.remove(tmp_file_path)

    async def generate_resume_from_pdf_bytes(self, pdf_bytes: bytes) -> Dict[str, Any]:
        """
        Given PDF bytes, extracts and returns a final JSON resume by:
        - Getting external OCR result
        - Combining them via an additional LLM call
        - Repairing the final JSON
        """
        final_result = await self._parse_pdf_bytes_async(pdf_bytes)
        return final_result