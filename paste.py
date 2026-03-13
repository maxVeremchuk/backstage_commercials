import os
import re
import json
import base64
import mimetypes
from PIL import Image
from openai import OpenAI
import dotenv

dotenv.load_dotenv()

# ----------------------------------------------------
# OpenAI / Nova client
# ----------------------------------------------------

client = OpenAI(
    api_key=os.getenv("NOVA_API_KEY"),
    base_url="https://api.nova.amazon.com/v1"
)

# ----------------------------------------------------
# Encode image
# ----------------------------------------------------

def encode_image(path):
    mime = mimetypes.guess_type(path)[0]

    with open(path, "rb") as f:
        data = base64.b64encode(f.read()).decode()

    return mime, data


# ----------------------------------------------------
# Safe JSON extraction
# ----------------------------------------------------

def extract_json(text):

    if text is None:
        raise ValueError("Empty model response")

    text = text.strip()

    match = re.search(r"\{.*\}", text, re.DOTALL)

    if not match:
        raise ValueError(f"No JSON found:\n{text}")

    json_text = match.group(0)

    return json.loads(json_text)


# ----------------------------------------------------
# Paste product into image
# ----------------------------------------------------

def paste_product(background_path, product_path, bbox, output_path):

    bg = Image.open(background_path).convert("RGBA")
    prod = Image.open(product_path).convert("RGBA")

    W, H = bg.size

    x = int(bbox["x"] * W)
    y = int(bbox["y"] * H)
    w = int(bbox["width"] * W)
    h = int(bbox["height"] * H)

    prod = prod.resize((w, h), Image.Resampling.LANCZOS)

    # Use the alpha channel as mask for transparent parts
    bg.paste(prod, (x, y), prod)

    # Convert back to RGB for saving as PNG
    bg = bg.convert("RGB")

    bg.save(output_path, "PNG")

# ----------------------------------------------------
# Placement prompt
# ----------------------------------------------------

placement_prompt = """
You are an AI marketing assistant specialized in realistic product placement.

Place a coffee jar naturally in the image.

Rules:
- Must be in the BACKGROUND
- Must be BEHIND people
- Must sit on a surface
- Must NOT float
- Look for empty space on the surface to place the product.

Coordinates must be normalized (0..1).

Return JSON:

{
 "placement_reason": "...",
 "support_surface": "...",
 "bounding_box": {
    "x": float,
    "y": float,
    "width": float,
    "height": float
 }
}
"""


# ----------------------------------------------------
# Adjustment prompt (for regeneration)
# ----------------------------------------------------

adjustment_prompt = """
You are an AI marketing assistant specialized in realistic product placement.

The product was previously placed but needs adjustment.

Previous placement had issues. Adjust the coffee jar position slightly.

Rules:
- Must be in the BACKGROUND
- Must be BEHIND people
- Must sit on a surface
- Must NOT float

ead 

Coordinates must be normalized (0..1).

Adjustment guidelines:
- To move left: decrease x
- To move right: increase x
- To move up: decrease y
- To move down: increase y
- To make smaller: decrease width and height
- To make larger: increase width and height

Return JSON:

{
 "placement_reason": "...",
 "support_surface": "...",
 "bounding_box": {
    "x": float,
    "y": float,
    "width": float,
    "height": float
 }
}
"""


# ----------------------------------------------------
# Evaluation prompt
# ----------------------------------------------------

evaluation_prompt = """
You are verifying whether a product placement looks realistic.

You are given:
- the image with the product inserted
- the previous coordinates

Evaluate if the placement looks correct.

Criteria:
- object sits on surface (table, desk, shelf, etc.)
- not floating
- correct scale
- logical location
- in the background

It is ok if object covers some people. It should be logically places on surface. 
If object covers persosn head it is ok.
if object convers floathing in front of other object it is not ok.

Return JSON:

{
 "valid": true or false,
 "reason": "...",
 "issues": "describe specific problems if any"
}

Set valid=true if the product blends reasonably well into the image.
Set valid=false if there are clear issues (floating, wrong scale, overlapping people, etc).
"""


# ----------------------------------------------------
# Ask placement model
# ----------------------------------------------------

def ask_placement_model(image_path, user_text, previous_bbox=None):

    mime, b64 = encode_image(image_path)

    prompt = placement_prompt if previous_bbox is None else adjustment_prompt

    user_message = user_text
    if previous_bbox is not None:
        user_message += f"\n\nPrevious bbox that had issues: {json.dumps(previous_bbox)}"

    response = client.chat.completions.create(

        model="nova-2-lite-v1",

        temperature=0,

        response_format={"type": "json_object"},

        messages=[
            {
                "role": "system",
                "content": prompt
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": user_message},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{mime};base64,{b64}"
                        }
                    }
                ]
            }
        ],

        max_tokens=600
    )

    result = response.choices[0].message.content

    print("\nPLACEMENT MODEL RESPONSE:")
    print(result)

    return result


# ----------------------------------------------------
# Ask evaluation model
# ----------------------------------------------------

def ask_evaluation_model(image_path, bbox):

    mime, b64 = encode_image(image_path)

    user_text = f"Evaluate the product placement. Current bbox: {json.dumps(bbox)}"

    response = client.chat.completions.create(

        model="nova-2-lite-v1",

        temperature=0,

        response_format={"type": "json_object"},

        messages=[
            {
                "role": "system",
                "content": evaluation_prompt
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": user_text},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{mime};base64,{b64}"
                        }
                    }
                ]
            }
        ],

        max_tokens=600
    )

    result = response.choices[0].message.content

    print("\nEVALUATION MODEL RESPONSE:")
    print(result)

    return result


# ----------------------------------------------------
# Recursive placement loop
# ----------------------------------------------------

def recursive_placement(background, product, max_iters=6):

    current_bbox = None
    current_image = background
    previous_bbox = None

    for step in range(max_iters):

        print("\n============================")
        print("ITERATION", step)
        print("============================")

        try:

            # Step 1: Get placement from placement model
            if step == 0:
                result = ask_placement_model(
                    background,
                    "Place the coffee jar in the image"
                )
            else:
                result = ask_placement_model(
                    background,
                    "Adjust the coffee jar placement based on previous issues",
                    previous_bbox=previous_bbox
                )

            data = extract_json(result)
            current_bbox = data["bounding_box"]

            print("Proposed bbox:", current_bbox)

            # Step 2: Paste product with proposed bbox
            output_img = f"placement_step_{step}.png"

            paste_product(
                background,
                product,
                current_bbox,
                output_img
            )

            current_image = output_img

            # Step 3: Evaluate the placement with evaluation model
            eval_result = ask_evaluation_model(current_image, current_bbox)

            eval_data = extract_json(eval_result)

            if eval_data["valid"]:

                print("✓ Placement approved by evaluation model")
                print(f"Reason: {eval_data.get('reason', 'N/A')}")

                return current_image

            else:

                print("✗ Placement rejected by evaluation model")
                print(f"Reason: {eval_data.get('reason', 'N/A')}")
                print(f"Issues: {eval_data.get('issues', 'N/A')}")

                # Save bbox for next iteration
                previous_bbox = current_bbox

        except Exception as e:

            print("ERROR:", e)
            print("Retrying iteration...")

            continue

    print("Max iterations reached without approval")

    return current_image


# ----------------------------------------------------
# Run
# ----------------------------------------------------

background = "hs.png"
product = "timhortons_nobg.png"

final_image = recursive_placement(background, product)

print("\nFinal image saved:", final_image)