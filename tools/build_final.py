"""根据审核结果（要）生成训练集：脸部裁切 + 全身图。"""
import json
import pathlib

from PIL import Image

ROOT = pathlib.Path(r"E:\RentAGirl")
CAND = ROOT / "review_img" / "candidates2"
VOTES = ROOT / "review_img" / "candidates2_votes.jsonl"
OUT = ROOT / "lora_data" / "train_final"
KEY = "chizuru, anime screenshot, 1girl, brown hair, brown eyes, brown eyes"


def main():
    last = {}
    for line in VOTES.read_text(encoding="utf-8").splitlines():
        try:
            v = json.loads(line)
        except Exception:
            continue
        last[v["id"]] = v["vote"]

    yes = [i for i, v in last.items() if v == "yes"]
    print("要:", len(yes))

    OUT.mkdir(parents=True, exist_ok=True)
    for f in OUT.glob("*"):
        f.unlink()

    n = 0
    for name in sorted(yes):
        p = CAND / name
        if not p.exists():
            continue
        im = Image.open(p).convert("RGB")
        w, h = im.size
        # 脸部偏重方形裁切
        side = min(w, int(h * 0.95))
        left = (w - side) // 2
        top = 0 if h <= side else int((h - side) * 0.06)
        face = im.crop((left, top, left + side, top + side)).resize((512, 512), Image.LANCZOS)
        face.save(OUT / f"{n:04d}.png")
        (OUT / f"{n:04d}.txt").write_text(KEY + ", upper body", encoding="utf-8")
        n += 1

    print("训练集:", n)


if __name__ == "__main__":
    main()
