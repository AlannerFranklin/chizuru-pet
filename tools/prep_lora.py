"""准备 LoRA 训练集：统一裁剪/缩放成 512x512，写 caption。"""
import pathlib

from PIL import Image

RAW = pathlib.Path(r"E:\RentAGirl\lora_data")
KEEP = (RAW / "keep.txt").read_text(encoding="utf-8").splitlines()
OUT = RAW / "train"
OUT.mkdir(parents=True, exist_ok=True)
SIZE = 512
CAPTION = "mizuhara chizuru, anime screenshot, brown hair, brown eyes"


def main():
    n = 0
    for p in KEEP:
        p = pathlib.Path(p)
        try:
            im = Image.open(p).convert("RGB")
        except Exception:
            continue
        w, h = im.size
        # 以人像为中心裁正方形：偏上一点（头在上半部）
        side = min(w, h)
        left = (w - side) // 2
        top = max(0, int((h - side) * 0.25))
        im = im.crop((left, top, left + side, top + side)).resize((SIZE, SIZE), Image.LANCZOS)
        out = OUT / f"{n:04d}.png"
        im.save(out)
        (OUT / f"{n:04d}.txt").write_text(CAPTION, encoding="utf-8")
        n += 1
    print("prepared", n)


if __name__ == "__main__":
    main()
