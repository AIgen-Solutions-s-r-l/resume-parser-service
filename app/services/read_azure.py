import os
import json
import asyncio
from dotenv import load_dotenv
load_dotenv()

async def analyze_read(file_path):
    from azure.core.credentials import AzureKeyCredential
    from azure.ai.documentintelligence import DocumentIntelligenceClient
    from azure.ai.documentintelligence.models import DocumentAnalysisFeature, AnalyzeResult, AnalyzeDocumentRequest

    endpoint = os.getenv("DOCUMENTINTELLIGENCE_ENDPOINT")
    key = os.getenv("DOCUMENTINTELLIGENCE_API_KEY")

    document_intelligence_client = DocumentIntelligenceClient(endpoint=endpoint, credential=AzureKeyCredential(key))

    # Analyze a document at a URL:
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
    
    # If analyzing a local document, remove the comment markers (#) at the beginning of these 11 lines.
    # Delete or comment out the part of "Analyze a document at a URL" above.
    # Replace <path to your sample file>  with your actual file path.
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
    
    # Save the JSON to a local file
    output_json_path = "output.json"
    with open(output_json_path, "w") as output_file:
        json.dump(content, output_file, indent=4)
    return json.dumps(content)
    
async def main():
    from azure.core.exceptions import HttpResponseError
    from dotenv import find_dotenv

    try:
        load_dotenv(find_dotenv())
        await analyze_read("../../FedericoElia.pdf")
    except HttpResponseError as error:
        # Examples of how to check an HttpResponseError
        # Check by error code:
        if error.error is not None:
            if error.error.code == "InvalidImage":
                print(f"Received an invalid image error: {error.error}")
            if error.error.code == "InvalidRequest":
                print(f"Received an invalid request error: {error.error}")
            # Raise the error again after printing it
            raise
        # If the inner error is None and then it is possible to check the message to get more information:
        if "Invalid request".casefold() in error.message.casefold():
            print(f"Uh-oh! Seems there was an invalid request: {error}")
        # Raise the error again
        raise
    
if __name__ == "__main__":
    asyncio.run(main())
    