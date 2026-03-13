import torch
from diffusers import AutoPipelineForImage2Image
from PIL import Image


# -------------------------------------------------
# Load model
# -------------------------------------------------

pipe = AutoPipelineForImage2Image.from_pretrained(
    "runwayml/stable-diffusion-v1-5",
    torch_dtype=torch.float16
).to("cuda")

pipe.enable_attention_slicing()
# pipe.enable_xformers_memory_efficient_attention()

pipe.safety_checker = None


# -------------------------------------------------
# Helper: resize image to SD resolution
# -------------------------------------------------

def resize_for_sd(image):

    w, h = image.size

    new_w = (w // 8) * 8
    new_h = (h // 8) * 8

    return image.resize((new_w, new_h))


# -------------------------------------------------
# Refine function
# -------------------------------------------------

def refine_image(input_path, output_path):

    image = Image.open(input_path).convert("RGB")
    image = resize_for_sd(image)

    prompt = (
        "photorealistic image, seamless product placement, "
        "object naturally resting on surface, realistic shadows, "
        "correct perspective, natural lighting, high detail"
    )

    negative_prompt = (
        "floating object, distorted object, extra objects, "
        "blurry, warped perspective, artifacts"
    )

    result = pipe(
        prompt=prompt,
        negative_prompt=negative_prompt,
        image=image,
        strength=0.22,          # ideal for blending
        guidance_scale=5,
        num_inference_steps=28
    ).images[0]

    result.save(output_path)

    return output_path


# -------------------------------------------------
# Run
# -------------------------------------------------

refined = refine_image(
    "placement_step_0.png",
    "placement_refined.png"
)

print("Refined image saved:", refined)