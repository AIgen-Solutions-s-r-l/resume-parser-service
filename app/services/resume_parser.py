import asyncio
import os
import logging
import base64
import re
import requests
import time

from io import BytesIO
from pathlib import Path
from typing import IO, List, Dict, Any
from tempfile import NamedTemporaryFile

from pdf2image import convert_from_path
from fix_busted_json import repair_json
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from app.services.prompt import BASE_OCR_PROMPT

logger = logging.getLogger(__name__)

class ResumeParser:
    """
    A single class that handles:
    - PDF to images conversion
    - OCR via a vision-capable LLM model
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
            model_name=self.model_name,
            openai_api_key=self.openai_api_key
        )

    def _process_file_to_images_base64(self, file_path: str, image_format: str = "PNG") -> List[str]:
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

    async def _convert_pdf_to_final_response(self, file_path: str, batch_size: int = 3) -> str:
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
            response = loop.run_until_complete(self._convert_pdf_to_final_response(file_path))
            return response
        finally:
            loop.close()

    def _parse_pdf_file(self, pdf_path: str) -> str:
        """
        Directly parse the PDF file using the LLM-based OCR and return raw JSON-like response.
        """
        return self._convert_sync(pdf_path)

    async def _external_ocr(self, pdf_path: str) -> str:
        """
        Sends the PDF to an external OCR service and polls for the result.
        Returns the markdown text if successful.
        """
        url = "https://www.datalab.to/api/v1/marker"
        headers = {"X-Api-Key": "kH9nBHsdrw123iikQAxjqc1nICmj7_T6GgBdGoWNb-0"}

        with open(pdf_path, 'rb') as f:
            form_data = {
                'file': ('test.pdf', f, 'application/pdf'),
                'langs': (None, "English"),
                'force_ocr': (None, True),
                'paginate': (None, False),
                'output_format': (None, 'markdown')
            }

            response = requests.post(url, files=form_data, headers=headers)
            data = response.json()

        max_polls = 300
        check_url = data["request_check_url"]

        for i in range(max_polls):
            time.sleep(2)
            response = requests.get(check_url, headers=headers)
            data = response.json()

            if data["status"] == "complete":
                return data['markdown']

        logger.error("External OCR service did not complete within polling limit.")
        return ""

    async def _combine_ocr_results(self, external_markdown: str, llm_response: str) -> str:
        """
        Calls the LLM again to combine the external OCR results (markdown) with
        the LLM-based OCR results (JSON-like) into a single cohesive JSON result.

        You can refine the prompt depending on the expected structure of the inputs and outputs.
        """
        combination_prompt = (
            "You are given two OCR outputs from the same resume:\n\n"
            "1) EXTERNAL OCR (markdown):\n"
            f"{external_markdown}\n\n"
            "2) LLM OCR (JSON-like):\n"
            f"{llm_response}\n\n"
            "Please combine them into a single well-structured JSON resume. "
            "Use the external OCR text to fill in any missing details from the LLM OCR result, "
            "and if there are conflicts, choose the most accurate information. "
            "Provide only the json code for the resume, without any explanations or additional text and also without ```json ```"
        )

        message = HumanMessage(content=combination_prompt)
        response = await self.llm.ainvoke([message])
        return response.content

    async def _parse_pdf_bytes_async(self, pdf_bytes: bytes) -> Dict[str, Any]:
        """
        Given PDF bytes, this writes them to a temporary file and then:
        1. Uses the external OCR service to get markdown result.
        2. Uses the LLM-based OCR to get JSON-like result.
        3. Calls another LLM prompt to combine both results into a final JSON.
        """
        loop = asyncio.get_event_loop()
        with NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_file:
            tmp_file.write(pdf_bytes)
            tmp_file_path = tmp_file.name

        try:
            # Step 1: Get external OCR result (markdown)
            external_markdown = await self._external_ocr(tmp_file_path)
            if not external_markdown.strip():
                logger.warning("External OCR returned empty or invalid content.")

            # Step 2: Get LLM-based OCR result (JSON-like string)
            llm_response = await loop.run_in_executor(None, lambda: self._parse_pdf_file(tmp_file_path))
            if not llm_response.strip():
                logger.warning("LLM OCR returned empty or invalid content.")

            # Step 3: Combine both results via another LLM call
            combined_response = await self._combine_ocr_results(external_markdown, llm_response)
            
            # Attempt to repair the final combined JSON
            try:
                final_json = repair_json(combined_response)
                print(final_json)
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
        - Getting LLM OCR result
        - Combining them via an additional LLM call
        - Repairing the final JSON
        """
        final_result = await self._parse_pdf_bytes_async(pdf_bytes)
        return final_result