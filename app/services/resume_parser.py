import asyncio
import os
import logging
import base64
import re

from io import BytesIO
from pathlib import Path
from typing import IO, List
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
    - JSON extraction and repair
    
    It encapsulates all logic previously spread across multiple classes.
    """

    def __init__(self, model_name: str = "gpt-4o-mini", openai_api_key: str = None):
        """
        :param model_name: Name of the model with vision + text capabilities.
        :param openai_api_key: Your OpenAI API key.
        """
        # Ensure the OPENAI_API_KEY environment variable or passed key is set
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
        Directly parse the PDF file and return the model's raw JSON response.
        """
        return self._convert_sync(pdf_path)

    async def _parse_pdf_bytes_async(self, pdf_bytes: bytes) -> str:
        """
        Given PDF bytes, this writes them to a temporary file and then parses.
        """
        loop = asyncio.get_event_loop()
        with NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_file:
            tmp_file.write(pdf_bytes)
            tmp_file_path = tmp_file.name

        try:
            # Run the parsing in an executor to avoid blocking
            response = await loop.run_in_executor(None, lambda: self._parse_pdf_file(tmp_file_path))
            return response
        except Exception as e:
            logger.error("Failed to parse PDF bytes.", extra={"error": str(e)})
            return ""
        finally:
            if os.path.exists(tmp_file_path):
                os.remove(tmp_file_path)

    async def generate_resume_from_pdf_bytes(self, pdf_bytes: bytes):
        """
        Given PDF bytes, extracts and returns the final JSON resume.
        """
        response = await self._parse_pdf_bytes_async(pdf_bytes)
        if not response.strip():
            logger.error("No content or invalid response from the model.")
            return {"error": "No content extracted or invalid response."}

        # Attempt to repair JSON if necessary
        try:
            resume_json = repair_json(response)
            return resume_json
        except Exception as e:
            logger.error("Failed to parse the returned JSON.", extra={"error": str(e)})
            return {"error": "Failed to parse the returned JSON."}