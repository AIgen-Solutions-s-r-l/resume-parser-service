import asyncio
import os
from pathlib import Path
from typing import IO
import logging
import os
from io import BytesIO
from tempfile import NamedTemporaryFile
from langchain_openai import ChatOpenAI
from fix_busted_json import repair_json
import asyncio
import base64
import re
from io import BytesIO
from pathlib import Path
from typing import IO, List

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage
from pdf2image import convert_from_path

from megaparse.core.parser import BaseParser
from megaparse.core.parser.entity import SupportedModel, TagEnum

logger = logging.getLogger(__name__)

from app.services.prompt import BASE_OCR_PROMPT

class MegaParseVision(BaseParser):
    def __init__(self, model: BaseChatModel, **kwargs):
        if hasattr(model, "model_name"):
            if not SupportedModel.is_supported(model.model_name):
                raise ValueError(
                    f"Invalid model name. MegaParseVision only supports models with vision capabilities. "
                    f"{model.model_name} is not supported."
                )
        self.model = model
        self.parsed_chunks: list[str] | None = None

    def process_file(self, file_path: str, image_format: str = "PNG") -> List[str]:
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

    def get_element(self, tag: TagEnum, chunk: str):
        pattern = rf"\[{tag.value}\]([\s\S]*?)\[/{tag.value}\]"
        all_elmts = re.findall(pattern, chunk)
        if not all_elmts:
            print(f"No {tag.value} found in the chunk")
            return []
        return [elmt.strip() for elmt in all_elmts]

    async def send_to_mlm(self, images_data: List[str]) -> str:
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
        response = await self.model.ainvoke([message])
        return str(response.content)

    async def convert(
        self,
        file_path: str | Path | None = None,
        file: IO[bytes] | None = None,
        batch_size: int = 3,
        **kwargs,
    ) -> str:
        if not file_path:
            raise ValueError("File_path should be provided to run MegaParseVision")

        if isinstance(file_path, Path):
            file_path = str(file_path)
        pdf_base64 = self.process_file(file_path)
        tasks = [
            self.send_to_mlm(pdf_base64[i : i + batch_size])
            for i in range(0, len(pdf_base64), batch_size)
        ]
        self.parsed_chunks = await asyncio.gather(*tasks)
        # In this integrated scenario, we expect the final chunk to already be the final JSON.
        # If the call is done in batches, the last response should be the final JSON (the prompt guides the model to do so).
        # Assuming that the model can handle multiple pages and still produce a single final JSON output.
        final_response = "\n".join(self.parsed_chunks).strip()
        return final_response

class MegaParse:
    def __init__(self, parser, format_checker=None) -> None:
        self.parser = parser
        self.format_checker = format_checker
        self.last_parsed_document: str = ""

    async def aload(
        self,
        file_path: Path | str | None = None,
        file: IO[bytes] | None = None,
        file_extension: str | None = "",
    ) -> str:
        if not (file_path or file):
            raise ValueError("Either file_path or file should be provided")
        if file_path and file:
            raise ValueError("Only one of file_path or file should be provided")

        if file_path and isinstance(file_path, str):
            file_path = Path(file_path)
        if file:
            file.seek(0)  # Ensure file pointer is at the start if a file object is used.

        try:
            parsed_document: str = await self.parser.convert(
                file_path=file_path, file=file
            )
        except Exception as e:
            raise ValueError(f"Error while parsing {file_path or 'provided file'}: {e}")

        self.last_parsed_document = parsed_document
        return parsed_document

    def load(self, file_path: Path | str) -> str:
        if isinstance(file_path, str):
            file_path = Path(file_path)

        try:
            loop = asyncio.get_event_loop()
            parsed_document: str = loop.run_until_complete(
                self.parser.convert(file_path=file_path)
            )
        except Exception as e:
            raise ValueError(f"Error while parsing {file_path}: {e}")

        self.last_parsed_document = parsed_document
        return parsed_document

    def save(self, file_path: Path | str) -> None:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w+", encoding="utf-8") as f:
            f.write(self.last_parsed_document)

class LLMFormatter:
    def __init__(self):
        # Note: Ensure the OPENAI_API_KEY environment variable is set to your correct API key.
        # The model name here should be compatible with vision + text capabilities as set up in MegaParseVision.
        self.llm = ChatOpenAI(model_name="gpt-4o-mini", openai_api_key=os.getenv("OPENAI_API_KEY"))

    def parse_pdf_with_megaparse(self, pdf_path: str) -> str:
        """
        Parse the PDF using MegaParseVision and return the final JSON resume.
        This now includes both the OCR step and the JSON resume generation in a single call.
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            # Reusing the same model for MegaParseVision
            model = ChatOpenAI(model="gpt-4o-mini", api_key=os.getenv("OPENAI_API_KEY"))  # type: ignore
            parser = MegaParseVision(model=model)
            megaparse = MegaParse(parser)

            # Use MegaParse to load the PDF and get the final JSON output directly
            response = megaparse.load(pdf_path)
            return response
        finally:
            loop.close()

    async def generate_resume_from_pdf_bytes(self, pdf_bytes: bytes):
        """
        Given PDF bytes, extracts and returns the final JSON resume in a single model call.
        """
        loop = asyncio.get_event_loop()

        with NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_file:
            tmp_file.write(pdf_bytes)
            tmp_file_path = tmp_file.name

        try:
            response = await loop.run_in_executor(None, lambda: self.parse_pdf_with_megaparse(tmp_file_path))
            if not response.strip():
                logger.error("No content or invalid response from the model.")
                return {"error": "No content extracted or invalid response."}
        except Exception as e:
            logger.error("Failed to generate JSON resume from PDF.", extra={"error": str(e)})
            return {"error": str(e)}
        finally:
            if os.path.exists(tmp_file_path):
                os.remove(tmp_file_path)

        # Attempt to repair JSON if necessary
        try:
            resume_json = repair_json(response)
            return resume_json
        except Exception as e:
            logger.error("Failed to parse the returned JSON.", extra={"error": str(e)})
            return {"error": "Failed to parse the returned JSON."}