"""把指定目录渲染成图片（可指定深度）。
用法: python render_dir.py "D:\\AIdub" 2 out.png
"""
import pathlib
import sys
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "D:/")
depth = int(sys.argv[2]) if len(sys.argv) > 2 else 2
out = pathlib.Path(sys.argv[3]) if len(sys.argv) > 3 else pathlib.Path(r"E:\RentAGirl\out\dir.png")


def human(n):
    for u in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024:
            return f"{n:.0f}{u}" if u == "B" else f"{n:.1f}{u}"
        n /= 1024
    return f"{n:.1f}PB"


lines = []


def walk(p, lvl):
    try:
        items = sorted(p.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))
    except OSError:
        return
    for it in items:
        try:
            st = it.stat()
            mt = datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m-%d %H:%M")
            size = "" if it.is_dir() else human(st.st_size)
        except OSError:
            continue
        kind = "📁" if it.is_dir() else "📄"
        lines.append((("  " * lvl) + f"{kind} {it.name}", size, mt))
        if it.is_dir() and lvl + 1 < depth:
            walk(it, lvl + 1)


walk(root, 0)

W = 1000
row_h = 30
top = 96
H = top + row_h * len(lines) + 40
img = Image.new("RGB", (W, H), (24, 25, 29))
d = ImageDraw.Draw(img)


def font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except OSError:
        return ImageFont.load_default()


f_title = font("C:/Windows/Fonts/msyhbd.ttc", 25)
f_head = font("C:/Windows/Fonts/msyh.ttc", 14)
f_row = font("C:/Windows/Fonts/msyh.ttc", 16)

d.text((26, 22), f"{root}", font=f_title, fill=(240, 240, 245))
d.text((26, 58), f"{len(lines)} 项 · 深度 {depth}", font=f_head, fill=(150, 153, 160))
x_size, x_time = 700, 820
d.text((x_size, top - 26), "大小", font=f_head, fill=(150, 153, 160))
d.text((x_time, top - 26), "修改时间", font=f_head, fill=(150, 153, 160))
d.line((20, top - 4, W - 20, top - 4), fill=(60, 62, 70), width=1)

y = top
for name, size, mt in lines:
    d.text((26, y), name, font=f_row, fill=(233, 233, 238) if "📁" in name else (200, 202, 208))
    if size:
        d.text((x_size, y), size, font=f_row, fill=(140, 143, 150))
    d.text((x_time, y), mt, font=f_row, fill=(120, 123, 130))
    y += row_h

img.save(out)
print("saved", out, img.size, "rows", len(lines))
