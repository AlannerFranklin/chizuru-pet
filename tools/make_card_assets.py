"""把原始插画做成圆角卡片立绘（不做抠图，避免手部/发丝被删）。"""
import pathlib
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

SRC = pathlib.Path(r"E:\dsh\dsh_wechat\媒体")
DST = pathlib.Path(r"E:\RentAGirl\assets_card")
DST.mkdir(parents=True, exist_ok=True)

jpgs = sorted(SRC.glob("*2026-10-28T03-19*.jpg"))

def rounded_mask(size, radius):
    m = Image.new("L", size, 0)
    d = ImageDraw.Draw(m)
    d.rounded_rectangle([0, 0, size[0] - 1, size[1] - 1], radius=radius, fill=255)
    return m

for i, f in enumerate(jpgs, 1):
    im = Image.open(f).convert("RGBA")
    w, h = im.size
    # 限制尺寸，避免桌宠太大
    scale = 900 / max(w, h) if max(w, h) > 900 else 1.0
    if scale != 1.0:
        im = im.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
        w, h = im.size
    radius = int(min(w, h) * 0.06)
    mask = rounded_mask((w, h), radius)
    # 外描边（白）
    border = Image.new("RGBA", (w, h), (255, 255, 255, 255))
    bmask = rounded_mask((w, h), radius)
    canvas = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    canvas.paste(border, (0, 0), bmask)
    inner = im.copy()
    inner.putalpha(mask)
    canvas.alpha_composite(inner)
    canvas.save(DST / f"chizuru_{i:02d}.png")
    print(f"chizuru_{i:02d}.png {w}x{h}")
