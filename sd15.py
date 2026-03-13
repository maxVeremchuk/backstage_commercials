import torch
import cv2
import numpy as np
from PIL import Image
from diffusers import AutoPipelineForInpainting

device = "cuda" if torch.cuda.is_available() else "cpu"

# ---------------------------
# Load lightweight inpainting pipeline
# ---------------------------
pipe = AutoPipelineForInpainting.from_pretrained(
    "stable-diffusion-v1-5/stable-diffusion-inpainting",
    torch_dtype=torch.float16 if device == "cuda" else torch.float32
)
pipe = pipe.to(device)
pipe.enable_model_cpu_offload()

# ---------------------------
# Load images
# ---------------------------
frame = Image.open("hs.png").convert("RGB").resize((512,512))
product = Image.open("timhortons.webp").convert("RGB").resize((180,180))

frame_np = np.array(frame)
prod_np = np.array(product)

# ---------------------------
# Choose position for object
# ---------------------------
x, y = 220, 260
h, w = prod_np.shape[:2]

# paste object roughly
frame_np[y:y+h, x:x+w] = prod_np

init_image = Image.fromarray(frame_np)

# ---------------------------
# Create mask for diffusion
# ---------------------------
mask = np.zeros((512,512), dtype=np.uint8)
mask[y:y+h, x:x+w] = 255
mask_img = Image.fromarray(mask)

# ---------------------------
# Prompt describing scene
# ---------------------------
prompt = "product naturally placed in the scene, realistic lighting, cinematic movie frame"

# ---------------------------
# Run diffusion blending
# ---------------------------
result = pipe(
    prompt=prompt,
    image=init_image,
    mask_image=mask_img,
    guidance_scale=7.5,
    num_inference_steps=30
).images[0]

# ---------------------------
# Save output
# ---------------------------
result.save("blended_frame.png")