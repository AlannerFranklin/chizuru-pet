"""用 CLIP 给候选图打分：越像"棕发褐眼的二次元女孩正面插画"分越高，剔除漫画页/多角色/文字。"""
import pathlib

import open_clip
import torch
from PIL import Image

ROOT = pathlib.Path(r"E:\RentAGirl\lora_data")
LIST = (ROOT / "pool_list.txt").read_text(encoding="utf-8").splitlines()

POS = [
    "official anime key visual of one girl with long brown hair and brown eyes",
    "anime screenshot of a single girl with long brown hair, upper body, plain background",
    "anime character portrait, long brown hair, brown eyes, white background",
]
NEG = [
    "black and white manga page with panels and speech bubbles",
    "poster with chinese text and many characters",
    "blonde anime girl with blue eyes",
    "silver haired anime girl",
    "group of anime characters standing together",
    "a photograph of a figurine or toy",
]


def main():
    dev = "cuda"
    model, _, preprocess = open_clip.create_model_and_transforms(
        "ViT-B-32", pretrained="laion2b_s34b_b79k", cache_dir=r"E:\cache\openclip")
    model = model.to(dev).eval()
    tok = open_clip.get_tokenizer("ViT-B-32")

    with torch.no_grad():
        tp = model.encode_text(tok(POS).to(dev))
        tn = model.encode_text(tok(NEG).to(dev))
        tp /= tp.norm(dim=-1, keepdim=True)
        tn /= tn.norm(dim=-1, keepdim=True)

    scored = []
    for line in LIST:
        p = pathlib.Path(line)
        try:
            im = preprocess(Image.open(p).convert("RGB")).unsqueeze(0).to(dev)
        except Exception:
            continue
        with torch.no_grad():
            f = model.encode_image(im)
            f /= f.norm(dim=-1, keepdim=True)
            sp = float((f @ tp.T).max())
            sn = float((f @ tn.T).max())
        scored.append((sp - sn, sp, sn, p))

    scored.sort(key=lambda x: -x[0])
    out = ROOT / "clip_rank.txt"
    with out.open("w", encoding="utf-8") as f:
        for s, sp, sn, p in scored:
            f.write(f"{s:.4f}\t{sp:.4f}\t{sn:.4f}\t{p}\n")
    print("scored", len(scored))
    for s, sp, sn, p in scored[:5]:
        print(f"{s:+.3f} {p.name}")
    for s, sp, sn, p in scored[-5:]:
        print(f"{s:+.3f} {p.name} (低)")


if __name__ == "__main__":
    main()
