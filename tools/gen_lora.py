"""用训练好的千鹤 LoRA 出图（diffusers + peft 直接加载）。
用法: python gen_lora.py --lora out/chizuru_lora_1200.safetensors --out E:\\RentAGirl\\out\\lora_test
"""
import argparse
import pathlib

import torch
from diffusers import StableDiffusionPipeline, UNet2DConditionModel
from peft import LoraConfig, get_peft_model, set_peft_model_state_dict
from safetensors.torch import load_file

BASE = pathlib.Path(r"E:\RentAGirl\lora_data\base_diffusers")
TRIGGER = "chizuru"
NEG = ("lowres, bad anatomy, bad hands, extra fingers, text, watermark, signature, "
       "worst quality, low quality, multiple girls, blurry, deformed")


def load_pipe(lora_path, rank=32):
    unet = UNet2DConditionModel.from_pretrained(str(BASE), subfolder="unet", torch_dtype=torch.float16)
    cfg = LoraConfig(r=rank, lora_alpha=rank, init_lora_weights="gaussian",
                     target_modules=["to_q", "to_k", "to_v", "to_out.0"])
    unet = get_peft_model(unet, cfg)
    sd = load_file(str(lora_path))
    set_peft_model_state_dict(unet, sd)
    unet = unet.merge_and_unload()
    # 把 LoRA 合并回 unet，然后塞进管道
    from diffusers.pipelines.stable_diffusion import StableDiffusionPipeline
    pipe = StableDiffusionPipeline.from_pretrained(str(BASE), torch_dtype=torch.float16,
                                                   safety_checker=None, requires_safety_checker=False)
    pipe.unet = unet.to(torch.float16).eval()
    pipe.to("cuda")
    pipe.enable_attention_slicing()
    return pipe


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lora", default=r"E:\RentAGirl\lora_data\out\chizuru_lora_2400.safetensors")
    ap.add_argument("--out", default=r"E:\RentAGirl\out\lora_test")
    ap.add_argument("--steps", type=int, default=30)
    ap.add_argument("--scale", type=float, default=7.5)
    args = ap.parse_args()

    out = pathlib.Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    pipe = load_pipe(args.lora)

    prompts = [
        f"{TRIGGER}, 1girl, standing on a theater stage, red curtains, spotlight, full body, anime style",
        f"{TRIGGER}, 1girl, walking on a lantern street at night, yukata, upper body, anime style",
        f"{TRIGGER}, 1girl, sitting in a cozy cafe, smiling, window light, anime style",
        f"{TRIGGER}, 1girl, portrait, school uniform, classroom, looking at viewer, anime style",
    ]
    for i, p in enumerate(prompts):
        g = torch.Generator(device="cuda").manual_seed(1234 + i)
        img = pipe(prompt=p, negative_prompt=NEG, num_inference_steps=args.steps,
                   guidance_scale=args.scale, height=768, width=512, generator=g).images[0]
        f = out / f"lora_{i:02d}.png"
        img.save(f)
        print("saved", f, flush=True)


if __name__ == "__main__":
    main()
