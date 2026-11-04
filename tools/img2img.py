"""图生图：用真实千鹤截图做底，换场景但保留她的脸。
用法: python img2img.py
"""
import pathlib

import torch
from diffusers import StableDiffusionImg2ImgPipeline
from PIL import Image

BASE = pathlib.Path(r"E:\RentAGirl\lora_data\base_diffusers")
SRC = pathlib.Path(r"E:\RentAGirl\assets_web")
OUT = pathlib.Path(r"E:\RentAGirl\out\img2img")
OUT.mkdir(parents=True, exist_ok=True)
NEG = ("lowres, bad anatomy, bad hands, extra fingers, text, watermark, signature, "
       "worst quality, low quality, multiple girls, blurry")

SCENES = [
    ("on a theater stage, red curtains, spotlight, standing", 0.45),
    ("walking on a lantern street at night, warm lights", 0.5),
    ("sitting in a cozy cafe, window light, coffee", 0.45),
    ("on a rooftop at sunset, city skyline", 0.5),
]


def main():
    pipe = StableDiffusionImg2ImgPipeline.from_pretrained(
        str(BASE), torch_dtype=torch.float16, safety_checker=None, requires_safety_checker=False)
    pipe.to("cuda")
    pipe.enable_attention_slicing()

    srcs = sorted(SRC.glob("*.png"))
    for i, (scene, strength) in enumerate(SCENES):
        src = Image.open(srcs[i % len(srcs)]).convert("RGB")
        src = src.resize((512, int(512 * src.height / src.width)) if src.width < src.height else (768, 512))
        src = src.crop((0, 0, src.width - src.width % 8, src.height - src.height % 8))
        prompt = f"1girl, mizuhara chizuru, brown hair, brown eyes, {scene}, anime style, detailed"
        g = torch.Generator(device="cuda").manual_seed(777 + i)
        img = pipe(prompt=prompt, negative_prompt=NEG, image=src, strength=strength,
                   num_inference_steps=30, guidance_scale=7.0, generator=g).images[0]
        p = OUT / f"i2i_{i:02d}.png"
        img.save(p)
        print("saved", p, flush=True)


if __name__ == "__main__":
    main()
