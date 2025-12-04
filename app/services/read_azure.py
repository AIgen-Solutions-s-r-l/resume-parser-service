"""Azure Document Intelligence integration for OCR processing."""
import json
from typing import Any

from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeResult, DocumentAnalysisFeature
from azure.core.credentials import AzureKeyCredential

from app.core.config import settings


async def analyze_read(file_path: str) -> str:
    """
    Analyze a document using Azure Document Intelligence OCR.

    Args:
        file_path: Path to the PDF file to analyze

    Returns:
        JSON string containing the extracted text content
    """
    endpoint = settings.document_intelligence_endpoint
    key = settings.document_intelligence_api_key

    document_intelligence_client = DocumentIntelligenceClient(
        endpoint=endpoint,
        credential=AzureKeyCredential(key),
    )

    with open(file_path, "rb") as f:
        poller = document_intelligence_client.begin_analyze_document(
            "prebuilt-read",
            analyze_request=f,
            features=[DocumentAnalysisFeature.LANGUAGES],
            content_type="application/octet-stream",
        )

    result: AnalyzeResult = poller.result()
    result_json = result.as_dict()
    content = result_json["content"]

    return json.dumps(content)
