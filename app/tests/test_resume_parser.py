# app/tests/test_resume_parser.py
"""
Unit tests for the ResumeParser service.
"""
import base64
from io import BytesIO
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock

import pytest

from app.services.resume_parser import ResumeParser


class TestResumeParserInitialization:
    """Tests for ResumeParser initialization."""

    def test_init_with_api_key(self):
        """Test initialization with explicit API key."""
        with patch("app.services.resume_parser.settings") as mock_settings:
            mock_settings.openai_api_key = None
            parser = ResumeParser(openai_api_key="test-key")
            assert parser.openai_api_key == "test-key"

    def test_init_with_settings_api_key(self):
        """Test initialization with API key from settings."""
        with patch("app.services.resume_parser.settings") as mock_settings:
            mock_settings.openai_api_key = "settings-key"
            parser = ResumeParser()
            assert parser.openai_api_key == "settings-key"

    def test_init_without_api_key_raises_error(self):
        """Test initialization without API key raises ValueError."""
        with patch("app.services.resume_parser.settings") as mock_settings:
            mock_settings.openai_api_key = None
            with pytest.raises(ValueError, match="OpenAI API key not provided"):
                ResumeParser(openai_api_key=None)

    def test_init_with_custom_model(self):
        """Test initialization with custom model name."""
        with patch("app.services.resume_parser.settings") as mock_settings:
            mock_settings.openai_api_key = "test-key"
            parser = ResumeParser(model_name="gpt-4o")
            assert parser.model_name == "gpt-4o"

    def test_set_executor(self):
        """Test setting the thread pool executor."""
        with patch("app.services.resume_parser.settings") as mock_settings:
            mock_settings.openai_api_key = "test-key"
            parser = ResumeParser()
            mock_executor = MagicMock()
            parser.set_executor(mock_executor)
            assert parser._executor == mock_executor


class TestPdfToImagesConversion:
    """Tests for PDF to images conversion."""

    @pytest.fixture
    def parser(self):
        """Create a ResumeParser instance for testing."""
        with patch("app.services.resume_parser.settings") as mock_settings:
            mock_settings.openai_api_key = "test-key"
            return ResumeParser()

    def test_process_file_to_images_base64_success(self, parser):
        """Test successful PDF to base64 images conversion."""
        mock_image = MagicMock()
        mock_image.save = MagicMock()

        with patch("app.services.resume_parser.convert_from_path") as mock_convert:
            mock_convert.return_value = [mock_image]

            # Mock the BytesIO save behavior
            def save_side_effect(buffer, format):
                buffer.write(b"fake_image_data")

            mock_image.save.side_effect = save_side_effect

            result = parser._process_file_to_images_base64("/fake/path.pdf")

            assert len(result) == 1
            assert isinstance(result[0], str)
            mock_convert.assert_called_once_with("/fake/path.pdf")

    def test_process_file_to_images_base64_error(self, parser):
        """Test PDF conversion error handling."""
        with patch("app.services.resume_parser.convert_from_path") as mock_convert:
            mock_convert.side_effect = Exception("PDF conversion failed")

            with pytest.raises(ValueError, match="Error processing PDF file"):
                parser._process_file_to_images_base64("/fake/path.pdf")


class TestLinkExtraction:
    """Tests for PDF link extraction."""

    @pytest.fixture
    def parser(self):
        """Create a ResumeParser instance for testing."""
        with patch("app.services.resume_parser.settings") as mock_settings:
            mock_settings.openai_api_key = "test-key"
            return ResumeParser()

    def test_extract_links_from_pdf_with_links(self, parser):
        """Test extracting links from PDF with embedded links."""
        mock_page = MagicMock()
        mock_page.get_links.return_value = [
            {"uri": "https://github.com/user"},
            {"uri": "https://linkedin.com/in/user"},
            {"kind": 1},  # Link without URI
        ]

        mock_doc = MagicMock()
        mock_doc.__len__ = MagicMock(return_value=1)
        mock_doc.load_page.return_value = mock_page

        with patch("app.services.resume_parser.fitz.open", return_value=mock_doc):
            result = parser.extract_links_from_pdf("/fake/path.pdf")

            assert len(result) == 2
            assert "https://github.com/user" in result
            assert "https://linkedin.com/in/user" in result

    def test_extract_links_from_pdf_no_links(self, parser):
        """Test extracting links from PDF without links."""
        mock_page = MagicMock()
        mock_page.get_links.return_value = []

        mock_doc = MagicMock()
        mock_doc.__len__ = MagicMock(return_value=1)
        mock_doc.load_page.return_value = mock_page

        with patch("app.services.resume_parser.fitz.open", return_value=mock_doc):
            result = parser.extract_links_from_pdf("/fake/path.pdf")
            assert result == []


class TestOcrCombination:
    """Tests for OCR result combination."""

    @pytest.fixture
    def parser(self):
        """Create a ResumeParser instance for testing."""
        with patch("app.services.resume_parser.settings") as mock_settings:
            mock_settings.openai_api_key = "test-key"
            return ResumeParser()

    @pytest.mark.asyncio
    async def test_combine_ocr_results_with_llm_ocr(self, parser):
        """Test combining OCR results when LLM OCR is present."""
        mock_response = MagicMock()
        mock_response.content = '{"name": "John Doe"}'
        parser.llm.ainvoke = AsyncMock(return_value=mock_response)

        result = await parser._combine_ocr_results(
            external_ocr="External OCR text",
            llm_ocr="LLM OCR text",
            links="https://github.com/user",
        )

        assert result == '{"name": "John Doe"}'
        parser.llm.ainvoke.assert_called_once()

    @pytest.mark.asyncio
    async def test_combine_ocr_results_without_llm_ocr(self, parser):
        """Test combining OCR results when LLM OCR is skipped (>5 pages)."""
        mock_response = MagicMock()
        mock_response.content = '{"name": "Jane Doe"}'
        parser.llm.ainvoke = AsyncMock(return_value=mock_response)

        result = await parser._combine_ocr_results(
            external_ocr="External OCR text",
            llm_ocr=None,
            links="https://linkedin.com/in/user",
        )

        assert result == '{"name": "Jane Doe"}'
        parser.llm.ainvoke.assert_called_once()


class TestSendImagesToModel:
    """Tests for sending images to the model."""

    @pytest.fixture
    def parser(self):
        """Create a ResumeParser instance for testing."""
        with patch("app.services.resume_parser.settings") as mock_settings:
            mock_settings.openai_api_key = "test-key"
            return ResumeParser()

    @pytest.mark.asyncio
    async def test_send_images_to_model_success(self, parser):
        """Test successful image sending to model."""
        mock_response = MagicMock()
        mock_response.content = "Parsed resume content"
        parser.llm.ainvoke = AsyncMock(return_value=mock_response)

        # Create fake base64 image data
        fake_image_data = base64.b64encode(b"fake_image").decode("utf-8")

        result = await parser._send_images_to_model([fake_image_data])

        assert result == "Parsed resume content"
        parser.llm.ainvoke.assert_called_once()


class TestParsePdfBytesAsync:
    """Tests for async PDF bytes parsing."""

    @pytest.fixture
    def parser(self):
        """Create a ResumeParser instance for testing."""
        with patch("app.services.resume_parser.settings") as mock_settings:
            mock_settings.openai_api_key = "test-key"
            return ResumeParser()

    @pytest.mark.asyncio
    async def test_parse_pdf_bytes_async_success_small_pdf(self, parser, sample_pdf_bytes):
        """Test successful parsing of small PDF (<=5 pages)."""
        mock_doc = MagicMock()
        mock_doc.__len__ = MagicMock(return_value=2)

        mock_page = MagicMock()
        mock_page.get_links.return_value = []
        mock_doc.load_page.return_value = mock_page

        with (
            patch("app.services.resume_parser.fitz.open", return_value=mock_doc),
            patch("app.services.resume_parser.analyze_read", new_callable=AsyncMock) as mock_azure,
            patch.object(parser, "_parse_pdf_file", return_value='{"llm": "response"}'),
            patch.object(
                parser,
                "_combine_ocr_results",
                new_callable=AsyncMock,
                return_value='{"combined": "result"}',
            ),
            patch("app.services.resume_parser.repair_json", return_value={"final": "json"}),
            patch("app.services.resume_parser.NamedTemporaryFile") as mock_temp,
            patch("app.services.resume_parser.os.path.exists", return_value=True),
            patch("app.services.resume_parser.os.remove"),
        ):
            mock_temp.return_value.__enter__.return_value.name = "/tmp/test.pdf"
            mock_azure.return_value = '{"azure": "ocr"}'

            result = await parser._parse_pdf_bytes_async(sample_pdf_bytes)

            assert result == {"final": "json"}

    @pytest.mark.asyncio
    async def test_parse_pdf_bytes_async_success_large_pdf(self, parser, sample_pdf_bytes):
        """Test successful parsing of large PDF (>5 pages) - skips LLM OCR."""
        mock_doc = MagicMock()
        mock_doc.__len__ = MagicMock(return_value=10)

        mock_page = MagicMock()
        mock_page.get_links.return_value = []
        mock_doc.load_page.return_value = mock_page

        with (
            patch("app.services.resume_parser.fitz.open", return_value=mock_doc),
            patch("app.services.resume_parser.analyze_read", new_callable=AsyncMock) as mock_azure,
            patch.object(
                parser,
                "_combine_ocr_results",
                new_callable=AsyncMock,
                return_value='{"combined": "result"}',
            ),
            patch("app.services.resume_parser.repair_json", return_value={"final": "json"}),
            patch("app.services.resume_parser.NamedTemporaryFile") as mock_temp,
            patch("app.services.resume_parser.os.path.exists", return_value=True),
            patch("app.services.resume_parser.os.remove"),
        ):
            mock_temp.return_value.__enter__.return_value.name = "/tmp/test.pdf"
            mock_azure.return_value = '{"azure": "ocr"}'

            result = await parser._parse_pdf_bytes_async(sample_pdf_bytes)

            assert result == {"final": "json"}

    @pytest.mark.asyncio
    async def test_parse_pdf_bytes_async_json_repair_failure(self, parser, sample_pdf_bytes):
        """Test handling of JSON repair failure."""
        mock_doc = MagicMock()
        mock_doc.__len__ = MagicMock(return_value=2)

        mock_page = MagicMock()
        mock_page.get_links.return_value = []
        mock_doc.load_page.return_value = mock_page

        with (
            patch("app.services.resume_parser.fitz.open", return_value=mock_doc),
            patch("app.services.resume_parser.analyze_read", new_callable=AsyncMock) as mock_azure,
            patch.object(parser, "_parse_pdf_file", return_value='{"llm": "response"}'),
            patch.object(
                parser,
                "_combine_ocr_results",
                new_callable=AsyncMock,
                return_value="invalid json",
            ),
            patch(
                "app.services.resume_parser.repair_json",
                side_effect=Exception("JSON repair failed"),
            ),
            patch("app.services.resume_parser.NamedTemporaryFile") as mock_temp,
            patch("app.services.resume_parser.os.path.exists", return_value=True),
            patch("app.services.resume_parser.os.remove"),
        ):
            mock_temp.return_value.__enter__.return_value.name = "/tmp/test.pdf"
            mock_azure.return_value = '{"azure": "ocr"}'

            result = await parser._parse_pdf_bytes_async(sample_pdf_bytes)

            assert "error" in result
            assert result["error"] == "Failed to parse the combined JSON."


class TestGenerateResumeFromPdfBytes:
    """Tests for the main public method."""

    @pytest.fixture
    def parser(self):
        """Create a ResumeParser instance for testing."""
        with patch("app.services.resume_parser.settings") as mock_settings:
            mock_settings.openai_api_key = "test-key"
            return ResumeParser()

    @pytest.mark.asyncio
    async def test_generate_resume_from_pdf_bytes(self, parser, sample_pdf_bytes):
        """Test the main entry point for resume generation."""
        expected_result = {"name": "John Doe", "email": "john@example.com"}

        with patch.object(
            parser,
            "_parse_pdf_bytes_async",
            new_callable=AsyncMock,
            return_value=expected_result,
        ):
            result = await parser.generate_resume_from_pdf_bytes(sample_pdf_bytes)

            assert result == expected_result
            parser._parse_pdf_bytes_async.assert_called_once_with(sample_pdf_bytes)
