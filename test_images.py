import os
import base64
import mimetypes
from openai import OpenAI
import dotenv

dotenv.load_dotenv()

client = OpenAI(
    api_key=os.getenv("NOVA_API_KEY"),
    base_url="https://api.nova.amazon.com/v1"
)

def encode_image(path):
    mime = mimetypes.guess_type(path)[0]
    with open(path, "rb") as f:
        data = base64.b64encode(f.read()).decode()
    return mime, data

image_path = "tom2.jpg"
mime, base64_image = encode_image(image_path)


system_prompt = """
You are an AI product discovery assistant.

Your task is to analyze the provided image and identify objects that correspond to consumer products that could realistically be sold on Amazon.

IMPORTANT: The product names must be simple and compatible with common object detection classes (such as YOLO). This means the name should usually be 1–2 words describing the object type.

Instructions:

1. Carefully inspect the image and detect objects that correspond to real consumer products.
2. Only include objects that could realistically be purchased online (electronics, furniture, clothing, home goods, accessories, tools, kitchen items, etc.).
3. Ignore objects that are not purchasable products (people, buildings, sky, animals, scenery, etc.).
4. For each detected product:
   - Provide a **simple object name (1–2 words)** that corresponds to a common detection class (examples: laptop, mug, keyboard, chair, backpack, lamp).
   - If multiple similar objects exist, add a **color or simple distinguishing attribute** to the name (example: "green teapot", "yellow teapot", "black mug").
   - Do NOT include long descriptions in the name.
5. Provide additional information in separate fields:
   - category: a short product category.
   - properties: short product attributes such as color, size, material, or visible features.
   - reason: why this product may be interesting for a user to purchase.

Naming Rules:
- Prefer common YOLO-style object names.
- Use lowercase names.
- Keep names concise (1–2 words, optionally with a color).
- Examples of good names:
  laptop
  keyboard
  desk lamp
  black mug
  red backpack
  green teapot
- Avoid names like:
  "modern ergonomic wireless mechanical keyboard"
  "large stylish decorative ceramic coffee mug"

Return the result strictly in the following JSON format:

{
  "products": [
    {
      "name": "product name",
      "category": "product category",
      "properties": "product properties",
      "reason": "why this product might interest the user"
    }
  ]
}

Example:

{
  "products": [
    {
      "name": "laptop",
      "category": "electronics",
      "properties": "15-inch, black, slim design",
      "reason": "useful for work, study, and entertainment"
    },
    {
      "name": "white keyboard",
      "category": "computer accessories",
      "properties": "mechanical keyboard with white backlight",
      "reason": "improves typing speed and comfort"
    },
    {
      "name": "desk lamp",
      "category": "home office",
      "properties": "adjustable arm, warm LED light",
      "reason": "helps provide better lighting for reading and work"
    }
  ]
}

Only output JSON.
"""

image_path = "hs.png"
mime, base64_image = encode_image(image_path)

# coffee_jar_path = "timhortons.webp"
# mime, base64_coffee_jar = encode_image(coffee_jar_path)





system_prompt = """
You are an AI marketing assistant specialized in realistic product placement in images.

Your task is to determine the best natural location to place a product so that it blends realistically into the scene.

Product: a coffee jar.

Placement rules (very important):

1. The product must be placed in the BACKGROUND of the image.
2. The product must be BEHIND all visible people.
3. Never place the product in front of or overlapping any person.
4. The product MUST rest on a real physical support surface (table, shelf, counter, desk, cabinet, floor).
5. The product must NOT float in the air.

Surface alignment rule (critical):
- Identify the supporting surface where the product will sit.
- The bottom of the bounding box MUST align exactly with that surface.
- The bottom coordinate (y + height) must correspond to the top of the surface.
- The bounding box must not extend below the surface and must not float above it.

Good placement examples:
- Coffee jar sitting on a table behind people
- Coffee jar on a shelf in the background
- Coffee jar on a counter behind the scene

Bad placement examples:
- Floating in the air
- Hanging off an edge
- Intersecting with people
- Cutting through objects

Coordinates:
Use NORMALIZED coordinates between 0 and 1 relative to the image size.

Coordinate system:
- (0,0) = top-left corner
- (1,1) = bottom-right corner
- x increases to the right
- y increases downward

Return a bounding box representing the product placement.

Output format (JSON only):

{
  "placement_reason": "short explanation of the chosen surface",
  "support_surface": "table / shelf / counter / floor / etc",
  "bounding_box": {
    "x": <top_left_x_0_to_1>,
    "y": <top_left_y_0_to_1>,
    "width": <box_width_0_to_1>,
    "height": <box_height_0_to_1>,
    "bottom_alignment": <y_plus_height_value_0_to_1>
  }
}

Constraints:
- All values must be between 0 and 1.
- The bottom_alignment must equal (y + height).
- The bottom of the bounding box must align with the surface so the coffee jar appears to sit on it.
- The object must not float.

Return only valid JSON.
"""

response = client.chat.completions.create(
    model="nova-2-lite-v1",
    messages=[
        {
            "role": "system",
            "content": system_prompt
        },
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "Put the coffee jar in the best place in the image."},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{mime};base64,{base64_image}"
                    }
                }
            ]
        }
    ],
    max_tokens=800
)

print(response.choices[0].message.content)