"""把 D 盘目录渲染成一张图（比截图清楚）。"""
import pathlib
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

def human(n):
    for u in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024:
            return f"{n:.0f}{u}" if u == "B" else f"{n:.1f}{u}"
        n /= 1024
    return f"{n:.1f}PB"

def dir_size(p, limit=20000):
    tot = 0
    cnt = 0
    try:
        for f in p.rglob("*"):
            if f.is_file():
                try:
                    tot += f.stat().st_size
                    cnt += 1
                except OSError:
                    pass
            cnt += 1
            if cnt > limit:
                break
    except OSError:
        pass
    return tot

rows = []
for p in sorted(pathlib.Path("D:/").iterdir(), key=lambda x: x.name.lower()):
    try:
        st = p.stat()
        mtime = datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m-%d %H:%M")
    except OSError:
        continue
    if p.is_dir():
        rows.append((p.name, "文件夹", "", mtime))
    else:
        rows.append((p.name, "文件", human(st.st_size), mtime))

W = 900
row_h = 30
top = 90
H = top + row_h * len(rows) + 40
img = Image.new("RGB", (W, H), (24, 25, 29))
d = ImageDraw.Draw(img)

def font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except OSError:
        return ImageFont.load_default()

f_title = font("C:/Windows/Fonts/msyhbd.ttc", 26)
f_head = font("C:/Windows/Fonts/msyh.ttc", 15)
f_row = font("C:/Windows/Fonts/msyh.ttc", 17)

d.text((28, 24), "D:\\ 目录", font=f_title, fill=(240, 240, 245))
d.text((28, 58), f"共 {len(rows)} 项", font=f_head, fill=(150, 153, 160))

x_name, x_type, x_size, x_time = 28, 430, 540, 660
y = top - 26
d.text((x_name, y), "名称", font=f_head, fill=(150, 153, 160))
d.text((x_type, y), "类型", font=f_head, fill=(150, 153, 160))
d.text((x_size, y), "大小", font=f_head, fill=(150, 153, 160))
d.text((x_time, y), "修改时间", font=f_head, fill=(150, 153, 160))
d.line((20, top - 4, W - 20, top - 4), fill=(60, 62, 70), width=1)

y = top
for name, typ, size, mtime in rows:
    color = (233, 233, 238) if typ == "文件夹" else (200, 202, 208)
    d.text((x_name, y), name, font=f_row, fill=color)
    d.text((x_type, y), typ, font=f_row, fill=(140, 143, 150))
    if size:
        d.text((x_size, y), size, font=f_row, fill=(140, 143, 150))
    d.text((x_time, y), mtime, font=f_row, fill=(120, 123, 130))
    y += row_h

out = pathlib.Path(r"E:\RentAGirl\out\d_drive.png")
img.save(out)
print("saved", out, img.size)
