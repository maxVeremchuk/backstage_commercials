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
- Must be upper part of the image
- Change the size to fit it on the background.
- Must be BEHIND people
- Must sit on a surface
- Must NOT float
- Look for empty space on the surface to place the product.
- Try to put on more visible surface, sunny place, on the background.
- Do not cover people or their head.

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
- Look for the gap between objects to place the product.
- Must be BEHIND people
- Bigger part must be visible
- Must sit on a surface
- Must NOT float


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

evaluation_prompt_template = """
You are verifying whether an inserted product placement is physically believable.

You are given:
- the image with the product inserted
- the previous bounding box coordinates
- the product being evaluated: {product_description}

Your task is to approve the placement if the product can be physically placed there.

Main rule:
- The product must be touching and resting on a visible support surface such as:
  - shelf
  - table
  - desk
  - counter
  - cabinet top
  - ledge
  - floor (for according product) or grass or pavement for large products
  - other clearly visible horizontal support surface

Strict approval policy:
- Approve ONLY if the bottom of the product's bounding box aligns with the top of a real visible support surface.
- The product must look like it is standing on that surface, not floating in front of it.
- If the product is even slightly floating above the surface, mark invalid.
- If the product is intersecting too deeply into the surface, mark invalid.
- If there is no clear visible supporting surface directly under the product, mark invalid.
- If the product appears attached to air, wall, person, or unsupported background region, mark invalid.
- Reject if the product part is out of the screen and it is cutted (bbox is out of the image)
- Reject if the product is on the balck space of the frame.
- Reject if the product mostly on the human.

Additional criteria:
- correct scale relative to nearby objects
- logical location in the scene
- preferably in the background
- realistic physical support is more important than occlusion

Occlusion rules:
- It is NOT OK if the product appears to float in front of another object without being supported by a surface.
- It is NOT OK if the product blocks objects in a way that breaks physical realism.

Important:
- Be strict.
- Do not approve just because the placement looks roughly plausible.
- Approve only when there is clear contact between the product bottom and a visible support surface.

Return ONLY valid JSON:

{{
  "valid": true,
  "reason": "...",
  "issues": "describe specific problems if any"
}}

Set valid=true only if the product clearly touches and rests on a visible surface.
Set valid=false if there are any clear issues, especially:
- floating
- no visible support surface (for the ground, the bottom of the product's bounding box be on the ground.)
- bottom not aligned with surface top
- wrong scale
- physically implausible placement
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

def ask_evaluation_model(image_path, bbox, product_description):

    mime, b64 = encode_image(image_path)

    user_text = f"Evaluate the product placement. Current bbox: {json.dumps(bbox)}"

    evaluation_prompt = evaluation_prompt_template.format(product_description=product_description)

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

def recursive_placement(background, product, product_description, max_iters=6):
    """
    Recursively place product in background image until approved.
    
    Returns:
        tuple: (final_image_path, bbox_coords)
            bbox_coords is a dict with keys: x1, y1, x2, y2 (in pixels)
    """

    current_bbox = None
    current_image = background
    previous_bbox = None

    # Get image dimensions for pixel conversion
    bg = Image.open(background)
    W, H = bg.size

    for step in range(max_iters):

        print("\n============================")
        print("ITERATION", step)
        print("============================")

        try:

            # Step 1: Get placement from placement model
            if step == 0:
                result = ask_placement_model(
                    background,
                    f"Place the {product_description} in the image"
                )
            else:
                result = ask_placement_model(
                    background,
                    f"Adjust the {product_description} placement based on previous issues",
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
            eval_result = ask_evaluation_model(current_image, current_bbox, product_description)

            eval_data = extract_json(eval_result)

            if eval_data["valid"]:

                print("✓ Placement approved by evaluation model")
                print(f"Reason: {eval_data.get('reason', 'N/A')}")

                # Convert normalized bbox to pixel coordinates (x1, y1, x2, y2)
                x1 = int(current_bbox["x"] * W)
                y1 = int(current_bbox["y"] * H)
                x2 = x1 + int(current_bbox["width"] * W)
                y2 = y1 + int(current_bbox["height"] * H)
                
                bbox_coords = {
                    "x1": x1,
                    "y1": y1,
                    "x2": x2,
                    "y2": y2
                }

                return current_image, bbox_coords

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

    # Convert final bbox to pixel coordinates even if not approved
    if current_bbox:
        x1 = int(current_bbox["x"] * W)
        y1 = int(current_bbox["y"] * H)
        x2 = x1 + int(current_bbox["width"] * W)
        y2 = y1 + int(current_bbox["height"] * H)
        
        bbox_coords = {
            "x1": x1,
            "y1": y1,
            "x2": x2,
            "y2": y2
        }
    else:
        bbox_coords = None

    return current_image, bbox_coords


# ----------------------------------------------------
# Run
# ----------------------------------------------------

if __name__ == "__main__":
    background = "../dh_first.png"
    product = "../bike_nobg.png"
    product_description = "Bicycle" #"Tim Hortons 100% Arabica Original Blend"

    final_image, bbox_coords = recursive_placement(background, product, product_description)

    print("\nFinal image saved:", final_image)
    print("Bounding box (x1, y1, x2, y2):", bbox_coords)