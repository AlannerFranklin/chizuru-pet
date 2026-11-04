"""从 Counterfeit 底模训练千鹤 LoRA（UNet 注意力层，自写最简训练循环）。
用法: python train_lora.py [--steps 1200]
"""
import argparse
import json
import math
import pathlib
import random
import time

import torch
from diffusers import StableDiffusionPipeline, UNet2DConditionModel, AutoencoderKL
from peft import LoraConfig, get_peft_model
from PIL import Image
from torchvision import transforms

ROOT = pathlib.Path(r"E:\RentAGirl\lora_data")
CKPT = pathlib.Path(r"E:\ComfyUI\repo\models\checkpoints\Counterfeit-V2.5_fp16.safetensors")
DIFF_DIR = pathlib.Path(r"E:\RentAGirl\lora_data\base_diffusers")
OUT_DIR = pathlib.Path(r"E:\RentAGirl\lora_data\out")
OUT_DIR.mkdir(parents=True, exist_ok=True)
TRIGGER = "chizuru"
SIZE = 512


def convert_base():
    if (DIFF_DIR / "model_index.json").exists():
        return
    from diffusers import StableDiffusionPipeline
    pipe = StableDiffusionPipeline.from_single_file(
        str(CKPT), torch_dtype=torch.float16, safety_checker=None)
    pipe.save_pretrained(str(DIFF_DIR), safe_serialization=True)
    print("底模已转换为 diffusers 格式", flush=True)


DATA_DIR = ""
def load_data():
    items = []
    for img in sorted(pathlib.Path(DATA_DIR).glob("*.png")):
        cap = img.with_suffix(".txt")
        text = cap.read_text(encoding="utf-8").strip() if cap.exists() else TRIGGER
        items.append((img, text))
    return items


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--steps", type=int, default=1200)
    ap.add_argument("--lr", type=float, default=1e-4)
    ap.add_argument("--rank", type=int, default=16)
    ap.add_argument("--save_every", type=int, default=400)
    ap.add_argument("--data", default="")
    args = ap.parse_args()
    global DATA_DIR
    DATA_DIR = args.data or str(ROOT / "train2")

    convert_base()
    torch.backends.cuda.matmul.allow_tf32 = True
    dev = "cuda"

    unet = UNet2DConditionModel.from_pretrained(str(DIFF_DIR), subfolder="unet", torch_dtype=torch.float32)
    vae = AutoencoderKL.from_pretrained(str(DIFF_DIR), subfolder="vae", torch_dtype=torch.float32)
    pipe = StableDiffusionPipeline.from_pretrained(str(DIFF_DIR), torch_dtype=torch.float32,
                                                   safety_checker=None, requires_safety_checker=False)
    te, tok = pipe.text_encoder, pipe.tokenizer
    for m in (vae, te, unet):
        m.eval()
        for p in m.parameters():
            p.requires_grad_(False)
    vae.to(dev)
    te.to(dev)

    cfg = LoraConfig(r=args.rank, lora_alpha=args.rank, init_lora_weights="gaussian",
                     target_modules=["to_q", "to_k", "to_v", "to_out.0"])
    unet = get_peft_model(unet, cfg).to(dev)
    params = [p for p in unet.parameters() if p.requires_grad]
    print("可训练参数:", sum(p.numel() for p in params) / 1e6, "M", flush=True)

    opt = torch.optim.AdamW(params, lr=args.lr, betas=(0.9, 0.99), weight_decay=1e-2)
    tf = transforms.Compose([transforms.Resize(SIZE), transforms.CenterCrop(SIZE), transforms.ToTensor(),
                             transforms.Normalize([0.5], [0.5])])
    data = load_data()
    print("训练图:", len(data), "步数:", args.steps, flush=True)

    t0 = time.time()
    loss_acc = 0.0
    for step in range(1, args.steps + 1):
        img_path, text = random.choice(data)
        im = Image.open(img_path).convert("RGB")
        px = tf(im).unsqueeze(0).to(dev, dtype=torch.float32)
        with torch.no_grad():
            lat = vae.encode(px).latent_dist.sample() * 0.18215
            ids = tok(text, padding="max_length", truncation=True, max_length=77,
                      return_tensors="pt").input_ids.to(dev)
            emb = te(ids)[0].to(torch.float32)

        noise = torch.randn_like(lat)
        t = torch.randint(0, 1000, (1,), device=dev).long()
        a = pipe.scheduler.alphas_cumprod.to(dev)[t].view(-1, 1, 1, 1)
        noisy = a.sqrt() * lat + (1 - a).sqrt() * noise
        pred = unet(noisy, t, encoder_hidden_states=emb).sample
        loss = torch.nn.functional.mse_loss(pred.float(), noise.float())

        (loss / 4).backward()
        if step % 4 == 0:
            torch.nn.utils.clip_grad_norm_(params, 1.0)
            opt.step()
            opt.zero_grad(set_to_none=True)

        loss_acc += loss.item()
        if step % 50 == 0:
            el = time.time() - t0
            print(f"step {step}/{args.steps} loss {loss_acc/50:.4f} "
                  f"({el/step:.2f}s/step, 剩 {int((args.steps-step)*el/step)}s)", flush=True)
            loss_acc = 0.0
        if step % args.save_every == 0 or step == args.steps:
            out = OUT_DIR / f"chizuru_lora_{step}.safetensors"
            from peft import get_peft_model_state_dict
            from safetensors.torch import save_file
            sd = {k: v.contiguous().cpu() for k, v in get_peft_model_state_dict(unet).items()}
            save_file(sd, str(out))
            print("已保存", out, flush=True)

    print("完成", flush=True)


if __name__ == "__main__":
    main()
