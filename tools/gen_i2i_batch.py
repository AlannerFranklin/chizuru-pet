"""批量图生图：给视频每一句台词生成一张"千鹤在新场景里"的图（保留她的脸）。"""
import pathlib

import torch
from diffusers import StableDiffusionImg2ImgPipeline
from PIL import Image

BASE = pathlib.Path(r"E:\RentAGirl\lora_data\base_diffusers")
SRC = pathlib.Path(r"E:\RentAGirl\assets_web")
RAW = pathlib.Path(r"E:\RentAGirl\lora_data\raw")
OUT = pathlib.Path(r"E:\RentAGirl\assets_i2i")
OUT.mkdir(parents=True, exist_ok=True)

NEG = ("lowres, bad anatomy, bad hands, extra fingers, text, watermark, signature, "
       "worst quality, low quality, multiple girls, 2girls, blurry, deformed, "
       "oversaturated, shiny skin")

SCENES = [
    ("standing on a theater stage, red curtains, spotlight, upper body", 0.42),
    ("walking on a university campus, sunny day, trees, upper body", 0.50),
    ("sitting in a cozy cafe, warm window light, upper body", 0.46),
    ("standing behind a reception counter, smiling politely, warm interior", 0.48),
    ("on a stage, dramatic spotlight, looking determined, upper body", 0.42),
    ("in an empty rehearsal room, wooden floor, large window", 0.48),
    ("in a japanese tatami room, warm evening lamp, upper body", 0.50),
    ("at a dining table with home cooked food, warm light, smiling", 0.48),
    ("walking on a quiet evening street, waving hand, upper body", 0.50),
]


def base_pipeline():
    pipe = StableDiffusionImg2ImgPipeline.from_pretrained(
        str(BASE), torch_dtype=torch.float16, safety_checker=None, requires_safety_checker=False)
    pipe.to("cuda")
    pipe.enable_attention_slicing()
    return pipe


def pick_sources():
    pics = sorted(SRC.glob("*.png"))
    for p in sorted(RAW.glob("*.png")):
        pics.append(p)
    return pics


def main():
    pipe = base_pipeline()
    srcs = pick_sources()
    for i, (scene, strength) in enumerate(SCENES):
        src = Image.open(srcs[i % len(srcs)]).convert("RGB")
        w, h = src.size
        if h > w:
            nh = 640
            nw = max(8, int(round(w * nh / h / 8)) * 8)
        else:
            nw = 640
            nh = max(8, int(round(h * nw / w / 8)) * 8)
        src = src.resize((nw, nh), Image.LANCZOS)
        prompt = (f"1girl, mizuhara chizuru, brown hair, long hair, brown eyes, {scene}, "
                  f"anime style, detailed background, soft lighting")
        g = torch.Generator(device="cuda").manual_seed(9000 + i)
        img = pipe(prompt=prompt, negative_prompt=NEG, image=src, strength=strength,
                   num_inference_steps=32, guidance_scale=6.5, generator=g).images[0]
        p = OUT / f"i2i_{i:02d}.png"
        img.save(p)
        print("saved", p, flush=True)


if __name__ == "__main__":
    main()
