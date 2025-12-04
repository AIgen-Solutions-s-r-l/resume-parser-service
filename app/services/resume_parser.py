import asyncio
from concurrent.futures import ThreadPoolExecutor
import os
import base64
import fitz
from io import BytesIO
from typing import List, Dict, Any, Optional
from tempfile import NamedTemporaryFile
from pdf2image import convert_from_path
from fix_busted_json import repair_json
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

from app.core.config import settings
from app.core.logging_config import LogConfig
from app.services.prompt import (
    BASE_OCR_PROMPT,
    COMBINATION_OCR_PROMPT,
    SINGLE_CALL_PROMPT,
)
from app.services.read_azure import analyze_read


logger = LogConfig.get_logger()


class ResumeParser:
    """
    Resume parser using dual OCR strategy.

    Combines Azure Document Intelligence and OpenAI GPT-4o Vision for
    accurate resume parsing. Uses async patterns throughout for efficiency.

    Features:
    - Azure Document Intelligence for text extraction
    - OpenAI GPT-4o Vision for visual understanding (PDFs <= 5 pages)
    - LLM-powered combination of OCR results
    - Automatic JSON repair
    - Retry logic with exponential backoff
    """

    def __init__(
        self,
        model_name: str = "gpt-4o-mini",
        openai_api_key: Optional[str] = None,
        max_retries: int = 3,
        retry_delay: int = 5,
    ):
        """
        Initialize the resume parser.

        Args:
            model_name: OpenAI model name for vision and text processing
            openai_api_key: OpenAI API key (uses settings if not provided)
            max_retries: Maximum retry attempts for OCR operations
            retry_delay: Delay between retries in seconds
        """
        self.openai_api_key = openai_api_key or settings.openai_api_key
        if not self.openai_api_key:
            raise ValueError("OpenAI API key not provided.")

        self.model_name = model_name
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        # Initialize the ChatOpenAI client
        self.llm = ChatOpenAI(
            model_name=self.model_name,
            openai_api_key=self.openai_api_key,
        )
        self._executor: Optional[ThreadPoolExecutor] = None

    def set_executor(self, executor: ThreadPoolExecutor) -> None:
        """
        Inject the shared ThreadPoolExecutor.

        Args:
            executor: ThreadPoolExecutor for CPU-bound operations
        """
        self._executor = executor

    def _process_file_to_images_base64(
        self, file_path: str, image_format: str = "PNG"
    ) -> List[str]:
        """
        Convert PDF pages to base64-encoded images.

        This is a CPU-bound operation that should be run in a thread pool.

        Args:
            file_path: Path to the PDF file
            image_format: Output image format (PNG or JPEG)

        Returns:
            List of base64-encoded image strings

        Raises:
            ValueError: If PDF processing fails
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
            logger.error(
                "Failed to convert PDF to images",
                extra={"event_type": "pdf_conversion_error", "error": str(e)},
            )
            raise ValueError(f"Error processing PDF file: {str(e)}")

    async def _send_images_to_model(self, images_data: List[str]) -> str:
        """
        Send images to the LLM for OCR processing.

        Args:
            images_data: List of base64-encoded image strings

        Returns:
            Model response as string
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

    async def _process_images_async(self, file_path: str) -> List[str]:
        """
        Convert PDF to images asynchronously using thread pool.

        Args:
            file_path: Path to the PDF file

        Returns:
            List of base64-encoded image strings
        """
        loop = asyncio.get_running_loop()

        if self._executor:
            # Run CPU-bound image conversion in thread pool
            return await loop.run_in_executor(
                self._executor,
                self._process_file_to_images_base64,
                file_path,
            )
        else:
            # Fallback: run in default executor
            return await loop.run_in_executor(
                None,
                self._process_file_to_images_base64,
                file_path,
            )

    async def _convert_pdf_to_llm_ocr(
        self, file_path: str, batch_size: int = 5
    ) -> str:
        """
        Convert PDF to text using LLM-based OCR.

        Processes pages in batches for efficiency when dealing with
        multi-page documents.

        Args:
            file_path: Path to the PDF file
            batch_size: Number of pages to process per batch

        Returns:
            Combined OCR text from all pages
        """
        # Convert PDF to images in thread pool
        pdf_base64_list = await self._process_images_async(file_path)

        # Process images in batches concurrently
        tasks = [
            self._send_images_to_model(pdf_base64_list[i : i + batch_size])
            for i in range(0, len(pdf_base64_list), batch_size)
        ]

        parsed_chunks = await asyncio.gather(*tasks)
        return "\n".join(parsed_chunks).strip()

    def _extract_links_sync(self, pdf_file_path: str) -> List[str]:
        """
        Extract hyperlinks from PDF (synchronous).

        Args:
            pdf_file_path: Path to the PDF file

        Returns:
            List of URLs found in the PDF
        """
        doc = fitz.open(pdf_file_path)
        urls = []
        try:
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                links = page.get_links()

                for link in links:
                    if "uri" in link:
                        uri = link["uri"]
                        if uri:
                            urls.append(uri)
        finally:
            doc.close()
        return urls

    async def extract_links_from_pdf(self, pdf_file_path: str) -> List[str]:
        """
        Extract hyperlinks from PDF asynchronously.

        Args:
            pdf_file_path: Path to the PDF file

        Returns:
            List of URLs found in the PDF
        """
        loop = asyncio.get_running_loop()
        if self._executor:
            return await loop.run_in_executor(
                self._executor, self._extract_links_sync, pdf_file_path
            )
        return await loop.run_in_executor(
            None, self._extract_links_sync, pdf_file_path
        )

    async def _combine_ocr_results(
        self, external_ocr: str, llm_ocr: Optional[str], links: List[str]
    ) -> str:
        """
        Combine OCR results into a single JSON resume.

        Uses LLM to intelligently merge results from different OCR sources,
        resolving conflicts and ensuring completeness.

        Args:
            external_ocr: Text from Azure Document Intelligence
            llm_ocr: Text from GPT-4o Vision (None if skipped)
            links: List of URLs extracted from PDF

        Returns:
            Combined JSON resume string
        """
        links_str = "\n".join(links) if links else "No links found"

        if llm_ocr:
            combination_prompt = f"""
You are provided with three OCR outputs from the same resume:
1. **EXTERNAL OCR**:
{external_ocr}

2. **LLM OCR**:
{llm_ocr}

3. **EXTRACTED LINKS**:
{links_str}

Instructions:
- Combine them into a single well-structured JSON resume.
- Use the external OCR text and links to fill in missing details from the LLM OCR result.
- If there are conflicts, choose the most accurate information.
- Don't include a separate section for links - integrate them into relevant sections.
- Don't add fields not part of the provided JSON structure.
- Provide only the JSON code, without explanations or markdown formatting.
- In the projects section, include production titles and corresponding links.
"""
        else:
            combination_prompt = f"""
You are provided with two OCR outputs from the same resume:
1. **EXTERNAL OCR**:
{external_ocr}

2. **EXTRACTED LINKS**:
{links_str}

{SINGLE_CALL_PROMPT}
"""
        message = HumanMessage(content=combination_prompt)
        response = await self.llm.ainvoke([message])
        return response.content

    async def _parse_pdf_bytes_async(self, pdf_bytes: bytes) -> Dict[str, Any]:
        """
        Parse PDF bytes into structured resume JSON.

        Pipeline:
        1. Write bytes to temporary file
        2. Run Azure OCR and LLM OCR concurrently (if <= 5 pages)
        3. Extract links from PDF
        4. Combine results via LLM
        5. Repair and validate JSON

        Args:
            pdf_bytes: Raw PDF file content

        Returns:
            Parsed resume as dictionary
        """
        # Write PDF to temporary file
        with NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_file:
            tmp_file.write(pdf_bytes)
            tmp_file_path = tmp_file.name

        try:
            # Get page count
            doc = fitz.open(tmp_file_path)
            num_pages = len(doc)
            doc.close()

            logger.info(
                "Starting PDF parsing",
                extra={
                    "event_type": "pdf_parse_start",
                    "num_pages": num_pages,
                    "use_llm_ocr": num_pages <= 5,
                },
            )

            # Retry loop with exponential backoff
            for attempt in range(self.max_retries):
                try:
                    # Step 1: Run OCR tasks concurrently
                    if num_pages <= 5:
                        # Use both Azure and LLM OCR for better accuracy
                        external_ocr, llm_response = await asyncio.gather(
                            analyze_read(tmp_file_path),
                            self._convert_pdf_to_llm_ocr(tmp_file_path),
                        )
                    else:
                        # Large documents: Azure only (LLM would be too slow/expensive)
                        logger.debug(
                            "Skipping LLM OCR for large document",
                            extra={"num_pages": num_pages},
                        )
                        external_ocr = await analyze_read(tmp_file_path)
                        llm_response = None

                    # Step 2: Extract links (async)
                    links = await self.extract_links_from_pdf(tmp_file_path)

                    # Step 3: Combine results via LLM
                    combined_response = await self._combine_ocr_results(
                        external_ocr, llm_response, links
                    )

                    # Step 4: Repair JSON
                    try:
                        final_json = repair_json(combined_response)
                        logger.info(
                            "PDF parsing completed successfully",
                            extra={"event_type": "pdf_parse_complete"},
                        )
                        return final_json
                    except Exception as e:
                        logger.error(
                            "Failed to repair JSON",
                            extra={
                                "event_type": "json_repair_error",
                                "error": str(e),
                                "attempt": attempt + 1,
                            },
                        )
                        return {"error": "Failed to parse the combined JSON."}

                except Exception as e:
                    if attempt < self.max_retries - 1:
                        wait_time = self.retry_delay * (2 ** attempt)  # Exponential backoff
                        logger.warning(
                            f"Attempt {attempt + 1} failed, retrying...",
                            extra={
                                "event_type": "pdf_parse_retry",
                                "attempt": attempt + 1,
                                "wait_time": wait_time,
                                "error": str(e),
                            },
                        )
                        await asyncio.sleep(wait_time)
                    else:
                        logger.error(
                            "All retry attempts failed",
                            extra={
                                "event_type": "pdf_parse_failed",
                                "total_attempts": self.max_retries,
                                "error": str(e),
                            },
                        )
                        return {"error": "Failed to process PDF."}

        finally:
            # Always clean up temp file
            if os.path.exists(tmp_file_path):
                os.remove(tmp_file_path)

    async def generate_resume_from_pdf_bytes(self, pdf_bytes: bytes) -> Dict[str, Any]:
        """
        Generate structured JSON resume from PDF bytes.

        This is the main entry point for resume parsing. It orchestrates
        the entire OCR and parsing pipeline.

        Args:
            pdf_bytes: Raw PDF file content

        Returns:
            Parsed resume as dictionary, or error dict if parsing fails
        """
        return await self._parse_pdf_bytes_async(pdf_bytes)
