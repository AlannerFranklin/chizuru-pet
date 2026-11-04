"""用 v2（UNet+TE 双 LoRA）出图，可指定快照。"""
import argparse
import pathlib

import torch
from diffusers import StableDiffusionPipeline, UNet2DConditionModel
from peft import LoraConfig, get_peft_model, set_peft_model_state_dict
from safetensors.torch import load_file

BASE = pathlib.Path(r"E:\RentAGirl\lora_data\base_diffusers")
TRIGGER = "chizuru"
NEG = ("lowres, bad anatomy, bad hands, extra fingers, text, watermark, signature, "
       "worst quality, low quality, multiple girls, blurry, deformed, 2girls")

PROMPTS = [
    f"{TRIGGER}, anime screenshot, 1girl, full body, standing on a theater stage, red curtains, spotlight",
    f"{TRIGGER}, anime screenshot, 1girl, full body, walking on a lantern street at night, yukata",
    f"{TRIGGER}, anime screenshot, 1girl, full body, school uniform, standing in a classroom",
    f"{TRIGGER}, anime screenshot, 1girl, upper body, sitting in a cozy cafe, smiling, window light",
    f"{TRIGGER}, anime screenshot, 1girl, portrait, looking at viewer, smiling softly",
    f"{TRIGGER}, anime screenshot, 1girl, full body, standing on a rooftop at sunset, city skyline",
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lora", default=r"E:\RentAGirl\lora_data\out2\chizuru_v2_3000.safetensors")
    ap.add_argument("--out", default=r"E:\RentAGirl\out\lora_v2")
    ap.add_argument("--steps", type=int, default=30)
    args = ap.parse_args()

    out = pathlib.Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    sd = load_file(str(args.lora))
    su = {k[len("unet."):]: v for k, v in sd.items() if k.startswith("unet.")}
    st = {k[len("te."):]: v for k, v in sd.items() if k.startswith("te.")}

    unet = UNet2DConditionModel.from_pretrained(str(BASE), subfolder="unet", torch_dtype=torch.float32)
    unet = get_peft_model(unet, LoraConfig(r=32, lora_alpha=32, target_modules=["to_q", "to_k", "to_v", "to_out.0"]))
    set_peft_model_state_dict(unet, su)
    unet = unet.merge_and_unload().to(torch.float16)

    pipe = StableDiffusionPipeline.from_pretrained(str(BASE), torch_dtype=torch.float16,
                                                   safety_checker=None, requires_safety_checker=False)
    pipe.unet = unet
    if st:
        te = pipe.text_encoder
        te = get_peft_model(te, LoraConfig(r=8, lora_alpha=8, target_modules=["q_proj", "k_proj", "v_proj", "out_proj"]))
        set_peft_model_state_dict(te, st)
        pipe.text_encoder = te.merge_and_unload().to(torch.float16)
    pipe.to("cuda")
    pipe.enable_attention_slicing()

    for i, p in enumerate(PROMPTS):
        g = torch.Generator(device="cuda").manual_seed(2024 + i)
        img = pipe(prompt=p, negative_prompt=NEG, num_inference_steps=args.steps,
                   guidance_scale=6.5, height=768, width=512, generator=g).images[0]
        f = out / f"v2_{i:02d}.png"
        img.save(f)
        print("saved", f, flush=True)


if __name__ == "__main__":
    main()
