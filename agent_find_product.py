import os
import json
from dotenv import load_dotenv
load_dotenv()

AGENT_NAME = os.getenv('AGENT_FIND_ID')

def ask_nova_search_product_agent(client, input_image: str, text_prompt: str) -> dict[str, str]:
    response = client.chat.completions.create(
        model=AGENT_NAME,
        messages=[
            {"role": "user", "content": [{"type": "text", "text": text_prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": input_image
                        }
                    }]}
        ],
        extra_body={ 
            "system_tools" : ["nova_grounding"],  
        },
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "find_it_result",
                "schema": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "amazon_link": {"type": "array",
                                        "items": {"type": "string"}},
                        "external_link": {"type": "array",
                                        "items": {"type": "string"}},
                        "item_description": {"type": "string"},
                        "is_found": {"type": "boolean"},
                    },
                    "required": ["amazon_link", "external_link", "item_description", "is_found"]
                }
            }
        }
    )
    raw = response.choices[0].message.content
    return json.loads(raw[raw.index('{'):raw.index('}')+1])
