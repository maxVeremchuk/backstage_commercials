from pathlib import Path

import torch
from finegrain_toolbox.src.finegrain_toolbox.flux import Model, TextEncoder
from finegrain_toolbox.src.finegrain_toolbox.processors import product_placement
from huggingface_hub import hf_hub_download
from PIL import Image

from optimum.quanto import quantize, freeze, qfloat8

device = torch.device("cuda")
dtype = torch.bfloat16

torch.backends.cuda.matmul.allow_tf32 = True
torch.backends.cudnn.allow_tf32 = True

# Optional: slightly reduce fragmentation
os_env = __import__("os").environ
os_env.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")

model = Model.from_pretrained(
    "black-forest-labs/FLUX.1-Kontext-dev",
    device=device,
    dtype=dtype,
)
print("MODEL LOADED")


def try_enable_memory_efficient_attention(module, name="module"):
    for fn_name in [
        "enable_xformers_memory_efficient_attention",
        "set_use_memory_efficient_attention_xformers",
        "enable_memory_efficient_attention",
    ]:
        if hasattr(module, fn_name):
            try:
                getattr(module, fn_name)()
                print(f"[OK] {name}: {fn_name}")
                return True
            except Exception as e:
                print(f"[WARN] {name}: {fn_name} failed: {e}")
    return False

try_enable_memory_efficient_attention(model, "model")
if hasattr(model, "transformer"):
    try_enable_memory_efficient_attention(model.transformer, "model.transformer")

# quantize(model.transformer, weights=qfloat8)
# freeze(model.transformer)

text_encoder = TextEncoder.from_pretrained(
    "black-forest-labs/FLUX.1-Kontext-dev",
    device=device,
    dtype=dtype,
)

lora_path = Path(
    hf_hub_download(
        repo_id="finegrain/finegrain-product-placement-lora",
        filename="finegrain-placement-v1-rank8.safetensors",
    )
)

prompt = text_encoder.encode("Add the reference image of the product in the box to look natural.")#("Add this in the box")

model.transformer.load_lora_adapter(lora_path, adapter_name="inserter")



def place_product(scene_image, reference, bbox, product_description):
    prompt = text_encoder.encode(f"Add the reference image of the product {product_description} in the box to look natural.")#("Add this in the box")
    result = product_placement.process(
        model=model,
        scene=scene_image,
        reference=reference,
        bbox=bbox,
        prompt=prompt,
    )
    result.output.save("flux_output.png")
    return result.output. "flux_output.png"


if __name__ == "__main__":
    scene_image = Image.open("../first_hs.png")
    reference = Image.open("timhortons_nobg.png")
    bbox = (921, 302, 1074, 431)

    result = product_placement.process(
        model=model,
        scene=scene_image,
        reference=reference,
        bbox=bbox,
        prompt=prompt,
    )

    result.output.save("output_bbox.png")
