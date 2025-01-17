import os
import json

async def analyze_read(file_path):
    from azure.core.credentials import AzureKeyCredential
    from azure.ai.documentintelligence import DocumentIntelligenceClient
    from azure.ai.documentintelligence.models import DocumentAnalysisFeature, AnalyzeResult, AnalyzeDocumentRequest
    from dotenv import load_dotenv
    load_dotenv()

    endpoint = os.getenv("DOCUMENTINTELLIGENCE_ENDPOINT")
    key = os.getenv("DOCUMENTINTELLIGENCE_API_KEY")

    document_intelligence_client = DocumentIntelligenceClient(endpoint=endpoint, credential=AzureKeyCredential(key))

    # Analyze a document at a URL
    # formUrl = "https://raw.githubusercontent.com/Azure-Samples/cognitive-services-REST-api-samples/master/curl/form-recognizer/rest-api/read.png"
    # formUrl = "https://github.com/AIHawk-Startup/resume_service/blob/main/FedericoElia.pdf"
    # Replace with your actual formUrl:
    # If you use the URL of a public website, to find more URLs, please visit: https://aka.ms/more-URLs 
    # If you analyze a document in Blob Storage, you need to generate Public SAS URL, please visit: https://aka.ms/create-sas-tokens
    # poller = document_intelligence_client.begin_analyze_document(
    #     "prebuilt-read",
    #     AnalyzeDocumentRequest(url_source=formUrl),
    #     features=[DocumentAnalysisFeature.LANGUAGES]
    # )       
    
    # Analyze a document in a local file
    path_to_sample_document = file_path
    with open(path_to_sample_document, "rb") as f:
        poller = document_intelligence_client.begin_analyze_document(
            "prebuilt-read",
            analyze_request=f,
            features=[DocumentAnalysisFeature.LANGUAGES],
            content_type="application/octet-stream",
        )
    result: AnalyzeResult = poller.result()
    
    # Convert the analysis result to JSON
    result_json = result.as_dict()
    content = result_json["content"]
    # Save the string content to txt file:
    output = "output.txt"
    with open(output, "w") as output_file:
        output_file.write(content)
    return json.load(content)

