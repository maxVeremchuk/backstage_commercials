REGION_ID = "us-west-2"
MODEL_ID = "us.amazon.nova-2-omni-v1:0"
BEDROCK_ENDPOINT_URL = "https://bedrock-runtime.us-west-2.amazonaws.com"

READ_TIMEOUT_SEC = 3 * 60
MAX_RETRIES = 1

import boto3
from botocore.config import Config
import json
import timeit
from botocore.exceptions import ClientError
from IPython.display import Image, display
import base64

def analyze_image(image_path, text_input):
    """Analyze an image with text input using Amazon Bedrock Nova model."""
    # Read and encode image
    with open(image_path, "rb") as image_file:
        image_data = image_file.read()
    
    # Determine image format
    import os
    ext = os.path.splitext(image_path)[1].lower()
    image_format = 'jpeg' if ext in ['.jpg', '.jpeg'] else 'png' if ext == '.png' else 'jpeg'
    
    # Create Bedrock client
    config = Config(
        read_timeout=READ_TIMEOUT_SEC,
        retries={"max_attempts": MAX_RETRIES},
    )
    
    bedrock_runtime = boto3.client(
        service_name="bedrock-runtime",
        region_name=REGION_ID,
        #endpoint_url=BEDROCK_ENDPOINT_URL,
        config=config,
    )
    
    # Prepare request
    request = {
        "modelId": MODEL_ID,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"image": {"format": image_format, "source": {"bytes": image_data}}},
                    {"text": text_input},
                ],
            }
        ],
        "inferenceConfig": {"temperature": 0.1, "maxTokens": 10000},
    }
    
    # Make API call
    response = bedrock_runtime.converse(**request)
    return response

def process_response(response, input_image_path):
    """Process and display response content with input and output images."""
    # Display input image first
    print("== Input Image ==")
    display(Image(filename=input_image_path))
    
    response_content_list = response["output"]["message"]["content"]

    # Extract image content block
    image_content = next(
        (item for item in response_content_list if "image" in item),
        None,
    )

    # Extract text content block
    text_content = next(
        (item for item in response_content_list if "text" in item),
        None,
    )

    if text_content:
        print("== Text Output ==")
        print(text_content["text"])

    if image_content:
        print("== Output Image ==")
        image_bytes = image_content["image"]["source"]["bytes"]
        display(Image(data=image_bytes))
        
        
# INPUT_IMAGE_PATH = "kitchen.png"
# TEXT_INPUT = "You are given realestate listing image of an empty kitchen. Add bar stools to island, fruit bowl and some ceremic containers to kitchen for virual staging"

# try:
#     start = timeit.default_timer()
#     response = analyze_image(INPUT_IMAGE_PATH, TEXT_INPUT)
#     elapsed = timeit.default_timer() - start

#     print(f"Request took {elapsed:.2f} seconds")

#     process_response(response, INPUT_IMAGE_PATH)

# except ClientError as err:
#     print("Error occurred:")
#     print(err)
#     if hasattr(err, "response"):
#         print(json.dumps(err.response, indent=2))

import boto3

bedrock = boto3.client("bedrock", region_name="us-west-2")

resp = bedrock.list_foundation_models(byProvider="Amazon")
for m in resp["modelSummaries"]:
    print(m["modelId"], " | ", m.get("modelName"))