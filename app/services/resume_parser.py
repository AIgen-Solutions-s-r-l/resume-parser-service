import asyncio
from concurrent.futures import ThreadPoolExecutor
import os
import logging
import base64
import fitz
from io import BytesIO
from typing import List, Dict, Any
from tempfile import NamedTemporaryFile
from pdf2image import convert_from_path
from fix_busted_json import repair_json
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from app.services.prompt import (
    BASE_OCR_PROMPT,
    COMBINATION_OCR_PROMPT,
    SINGLE_CALL_PROMPT,
)
from app.services.read_azure import analyze_read


logger = logging.getLogger(__name__)


class ResumeParser:
    """
    A single class that handles:
    - External OCR service
    - JSON extraction and repair
    - Combining results from both approaches via another LLM call
    """

    def __init__(self, model_name: str = "gpt-4o-mini", openai_api_key: str = None):
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
            model_name=self.model_name, openai_api_key=self.openai_api_key
        )
        self._executor: ThreadPoolExecutor | None = None

    def set_executor(self, executor: ThreadPoolExecutor):
        """Inject the shared ThreadPoolExecutor after initialization."""
        self._executor = executor

    def _process_file_to_images_base64(
        self, file_path: str, image_format: str = "PNG"
    ) -> List[str]:
        """
        Converts a PDF file into a list of base64-encoded images (one per page).
        """
        try:
            images = convert_from_path(file_path)
            images_base64 = []
            for image in images:
                buffered = BytesIO()
                image.save(buffered, format=image_format)
                image_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")
                images_base64.append(image_base64)
            return images_base64
        except Exception as e:
            raise ValueError(f"Error processing PDF file: {str(e)}")

    async def _send_images_to_model(self, images_data: List[str]) -> str:
        """
        Sends a batch of base64-encoded images along with the OCR prompt to the model,
        and returns the model's response.
        """
        images_prompt = [
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{image_data}"},
            }
            for image_data in images_data
        ]

        message = HumanMessage(
            content=[
                {"type": "text", "text": BASE_OCR_PROMPT},
                *images_prompt,
            ],
        )
        response = await self.llm.ainvoke([message])
        return str(response.content)

    async def _convert_pdf_to_final_response(
        self, file_path: str, batch_size: int = 5
    ) -> str:
        """
        Orchestrates:
        - Converting PDF pages to images
        - Sending them to the model in batches
        - Combining the responses into a final JSON-like string
        """
        pdf_base64_list = self._process_file_to_images_base64(file_path)
        tasks = [
            self._send_images_to_model(pdf_base64_list[i : i + batch_size])
            for i in range(0, len(pdf_base64_list), batch_size)
        ]

        parsed_chunks = await asyncio.gather(*tasks)
        final_response = "\n".join(parsed_chunks).strip()
        return final_response

    def _convert_sync(self, file_path: str) -> str:
        """
        A synchronous wrapper to handle the async convert logic.
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            response = loop.run_until_complete(
                self._convert_pdf_to_final_response(file_path)
            )
            return response
        finally:
            loop.close()

    def _parse_pdf_file(self, pdf_path: str) -> str:
        """
        Directly parse the PDF file using the LLM-based OCR and return raw JSON-like response.
        """
        return self._convert_sync(pdf_path)

    def extract_links_from_pdf(self, pdf_file_path):
        doc = fitz.open(pdf_file_path)
        urls = []
        # Iterate over each page in the PDF
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)  # Get the page

            # Extract links from the page (links can be represented as actions)
            links = page.get_links()

            for link in links:
                if "uri" in link:
                    uri = link["uri"]
                    if uri:
                        urls.append(uri)
        return urls

    async def _combine_ocr_results(
        self, external_ocr: str, llm_ocr: str, links: str
    ) -> str:
        """
        Combine the results from the external OCR, LLM OCR if present and extracted links into a single JSON resume.
        """
        if llm_ocr:
            combination_prompt = f"""
                \nYou are provided with three OCR outputs from the same resume:
                1. **EXTERNAL OCR**:\n {external_ocr}
                2. **LLM OCR**:\n {llm_ocr}
                3. **LINKS OCR**:\n {links}

                Instructions:
                - Please combine them into a single well-structured JSON resume.
                - Use the external OCR text and the links OCR to fill in any missing details from the LLM OCR result
                - and if there are conflicts, choose the most accurate information.
                - Don't include a separate section for links.
                - Don't add any other section or field that is not part of the provided JSON structure.
                - Provide only the json code for the resume, without any explanations or additional text and also without ```json ```.
                - In the projects section, incorporate information from both OCRs, ensuring to include the production titles and links. Include the link URLs as they correspond to the specific productions mentioned.
                
            """
        else:  # Skipped the LLM OCR processing if the document has more than 5 pages
            combination_prompt = f"""
                \nYou are provided with two OCR outputs from the same resume:
                1. **EXTERNAL OCR**:\n {external_ocr}
                2. **LINKS OCR**:\n {links}
                
                {SINGLE_CALL_PROMPT}
            """
        # Send the combination prompt to file
        with open("combination_prompt.txt", "w") as f:
            f.write(combination_prompt)
        message = HumanMessage(content=combination_prompt)
        response = await self.llm.ainvoke([message])
        return response.content

    async def _parse_pdf_bytes_async(self, pdf_bytes: bytes) -> Dict[str, Any]:
        """
        Given PDF bytes, writes them to a temporary file and:
        - Create an EXTERNAL OCR with Azure
        - (Parses the PDF using LLM OCR) if pages <= 5
        - Extracts links from the PDF
        - Combines the results via another LLM call
        - Repairs the final JSON
        """
        loop = asyncio.get_event_loop()
        with NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_file:
            tmp_file.write(pdf_bytes)
            tmp_file_path = tmp_file.name

        attempt = 0
        max_retries = 3
        delay = 5
        doc = fitz.open(tmp_file_path)
        num_pages = len(doc)
        num_pages = 10 # FIXED: to force always no intermediate llm call
        while attempt < max_retries:
            try:
                # Step 1: Get external OCR and LLM response
                if num_pages <= 5:
                    # Proceed with the LLM response task if the document has 5 or fewer pages
                    external_ocr_task = analyze_read(tmp_file_path)
                    llm_response_task = loop.run_in_executor(
                        self._executor, lambda: self._parse_pdf_file(tmp_file_path)
                    )
                    external_ocr, llm_response = await asyncio.gather(
                        external_ocr_task, llm_response_task
                    )
                    # Write llm_response to json file
                    # import json
                    # with open("llm_response.json", "w") as f:
                    #     json.dump(llm_response[0], f)
                else:
                    # print("Document has more than 5 pages. Skipping LLM processing.")
                    external_ocr = await analyze_read(tmp_file_path)
                    # write external_ocr to file
                    # with open("external_ocr.txt", "w") as f:
                    #     f.write(external_ocr)
                    llm_response = None

                # Step 2: Extract links from the PDF
                links = self.extract_links_from_pdf(tmp_file_path)

                # Step 3: Combine both results via another LLM call
                combined_response = await self._combine_ocr_results(
                    external_ocr, llm_response, links
                )

                # Attempt to repair the final combined JSON
                try:
                    final_json = repair_json(combined_response)
                    return final_json
                except Exception as e:
                    logger.error(
                        "Failed to parse the combined JSON.", extra={"error": str(e)}
                    )
                    return {"error": "Failed to parse the combined JSON."}

            except Exception as e:
                attempt += 1
                if attempt < max_retries:
                    logger.warning(
                        f"Attempt {attempt} failed. Retrying in {delay} seconds...",
                        extra={"error": str(e)},
                    )
                    await asyncio.sleep(delay)  # Delay before retrying
                else:
                    logger.error("All retry attempts failed.", extra={"error": str(e)})
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
