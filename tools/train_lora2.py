"""LoRA v2：UNet + TextEncoder 双 LoRA + 余弦调度 + 多快照，专攻角色身份。
用法: python train_lora2.py --steps 3000
"""
import argparse
import pathlib
import random
import time

import torch
import torch.nn.functional as F
from diffusers import StableDiffusionPipeline, UNet2DConditionModel, AutoencoderKL
from peft import LoraConfig, get_peft_model, get_peft_model_state_dict
from PIL import Image, ImageFilter, ImageStat
from safetensors.torch import save_file
from torchvision import transforms

ROOT = pathlib.Path(r"E:\RentAGirl\lora_data")
SRC = ROOT / "raw"
DIFF_DIR = ROOT / "base_diffusers"
OUT_DIR = ROOT / "out2"
OUT_DIR.mkdir(parents=True, exist_ok=True)
SIZE = 512
TRIGGER = "chizuru"


def pick_best(n=110):
    """挑最清楚、最像动画截图的图，并做偏脸部的方形裁切。"""
    items = []
    for p in sorted(SRC.glob("*.png")):
        try:
            im = Image.open(p).convert("RGB")
        except Exception:
            continue
        w, h = im.size
        if min(w, h) < 560:
            continue
        sat = ImageStat.Stat(im.convert("HSV")).mean[1]
        if sat < 25:
            continue
        g = im.convert("L").resize((256, 256))
        lap = g.filter(ImageFilter.FIND_EDGES)
        sharp = ImageStat.Stat(lap).var[0]
        if sharp < 60:
            continue
        items.append((sharp, p, im))
    items.sort(key=lambda x: -x[0])
    return items[:n]


def prep(data_dir=None):
    OUT = ROOT / "train3"
    OUT.mkdir(exist_ok=True)
    for old in OUT.glob("*"):
        old.unlink()
    n = 0
    for sharp, p, im in pick_best():
        w, h = im.size
        side = min(w, int(h * 0.85))
        left = (w - side) // 2
        top = 0 if h <= side else int((h - side) * 0.1)
        crop = im.crop((left, top, left + side, top + side)).resize((SIZE, SIZE), Image.LANCZOS)
        crop.save(OUT / f"{n:04d}.png")
        cap = "chizuru, anime screenshot, 1girl, brown hair, brown eyes"
        if side < w:
            cap += ", upper body"
        (OUT / f"{n:04d}.txt").write_text(cap, encoding="utf-8")
        n += 1
    print("数据集:", n, flush=True)
    return OUT


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--steps", type=int, default=3000)
    ap.add_argument("--lr", type=float, default=1e-4)
    ap.add_argument("--te_lr", type=float, default=5e-5)
    ap.add_argument("--rank", type=int, default=32)
    ap.add_argument("--te_rank", type=int, default=8)
    ap.add_argument("--save_every", type=int, default=500)
    ap.add_argument("--data", default="")
    args = ap.parse_args()

    data_dir = pathlib.Path(args.data) if args.data else prep()
    dev = "cuda"

    vae = AutoencoderKL.from_pretrained(str(DIFF_DIR), subfolder="vae", torch_dtype=torch.float32)
    unet = UNet2DConditionModel.from_pretrained(str(DIFF_DIR), subfolder="unet", torch_dtype=torch.float32)
    pipe = StableDiffusionPipeline.from_pretrained(str(DIFF_DIR), torch_dtype=torch.float32,
                                                   safety_checker=None, requires_safety_checker=False)
    te, tok = pipe.text_encoder, pipe.tokenizer
    for m in (vae, te, unet):
        m.eval()
        for p in m.parameters():
            p.requires_grad_(False)
    vae.to(dev)
    te.to(dev)

    unet = get_peft_model(unet, LoraConfig(
        r=args.rank, lora_alpha=args.rank, init_lora_weights="gaussian",
        target_modules=["to_q", "to_k", "to_v", "to_out.0"])).to(dev)
    te = get_peft_model(te, LoraConfig(
        r=args.te_rank, lora_alpha=args.te_rank, init_lora_weights="gaussian",
        target_modules=["q_proj", "k_proj", "v_proj", "out_proj"])).to(dev)

    pu = [p for p in unet.parameters() if p.requires_grad]
    pt = [p for p in te.parameters() if p.requires_grad]
    opt = torch.optim.AdamW([{"params": pu, "lr": args.lr}, {"params": pt, "lr": args.te_lr}],
                            betas=(0.9, 0.99), weight_decay=1e-2)
    sched = torch.optim.lr_scheduler.OneCycleLR(
        opt, max_lr=[args.lr, args.te_lr], total_steps=args.steps, pct_start=0.05)

    files = sorted(data_dir.glob("*.png"))
    tf = transforms.Compose([transforms.ToTensor(), transforms.Normalize([0.5], [0.5])])
    print(f"图 {len(files)} 张, {args.steps} 步", flush=True)

    t0 = time.time()
    acc = 0.0
    for step in range(1, args.steps + 1):
        img_path = random.choice(files)
        text = img_path.with_suffix(".txt").read_text(encoding="utf-8").strip()
        px = tf(Image.open(img_path).convert("RGB")).unsqueeze(0).to(dev)
        with torch.no_grad():
            lat = vae.encode(px).latent_dist.sample() * 0.18215
            ids = tok(text, padding="max_length", truncation=True, max_length=77,
                      return_tensors="pt").input_ids.to(dev)
            emb = te(ids)[0]
        noise = torch.randn_like(lat)
        t = torch.randint(0, 1000, (1,), device=dev).long()
        a = pipe.scheduler.alphas_cumprod.to(dev)[t].view(-1, 1, 1, 1)
        noisy = a.sqrt() * lat + (1 - a).sqrt() * noise
        pred = unet(noisy, t, encoder_hidden_states=emb).sample
        loss = F.mse_loss(pred, noise)

        loss.backward()
        torch.nn.utils.clip_grad_norm_(pu + pt, 1.0)
        opt.step()
        sched.step()
        opt.zero_grad(set_to_none=True)

        acc += loss.item()
        if step % 50 == 0:
            el = time.time() - t0
            print(f"step {step}/{args.steps} loss {acc/50:.4f} ({el/step:.2f}s/step)", flush=True)
            acc = 0.0
        if step % args.save_every == 0 or step == args.steps:
            su = {f"unet.{k}": v.contiguous().cpu() for k, v in get_peft_model_state_dict(unet).items()}
            st = {f"te.{k}": v.contiguous().cpu() for k, v in get_peft_model_state_dict(te).items()}
            out = OUT_DIR / f"chizuru_v2_{step}.safetensors"
            save_file({**su, **st}, str(out))
            print("已保存", out, flush=True)
    print("完成", flush=True)


if __name__ == "__main__":
    main()
