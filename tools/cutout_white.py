"""把白底插画抠成透明立绘：从边缘 flood fill 掉连通的白色，保留衣服内部的白色。"""
import pathlib
import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage

SRC = pathlib.Path(r"E:\dsh\dsh_wechat\媒体\mvs8guty-e398169e-image-2026-10-28T14-52-18-838Z.jpg")
DST = pathlib.Path(r"E:\RentAGirl\assets_v3")
DST.mkdir(parents=True, exist_ok=True)

im = Image.open(SRC).convert("RGB")
arr = np.array(im).astype(np.int16)
h, w = arr.shape[:2]

# 近白像素
near_white = (arr[:, :, 0] > 238) & (arr[:, :, 1] > 238) & (arr[:, :, 2] > 238)

# 与边缘连通的白色区域 = 背景
lab, n = ndimage.label(near_white)
border_labels = set(lab[0, :]) | set(lab[-1, :]) | set(lab[:, 0]) | set(lab[:, -1])
border_labels.discard(0)
bg = np.isin(lab, list(border_labels))

# 稍微膨胀背景 1px，避免白边
bg = ndimage.binary_dilation(bg, np.ones((3, 3)))

alpha = np.where(bg, 0, 255).astype(np.uint8)
# 边缘羽化
a_img = Image.fromarray(alpha).filter(ImageFilter.GaussianBlur(0.8))

out = np.dstack([np.array(im), np.array(a_img)])
img = Image.fromarray(out, "RGBA")

# 裁到内容
bbox = Image.fromarray(alpha).getbbox()
if bbox:
    img = img.crop(bbox)

# 缩放到高度 760
if img.height > 760:
    s = 760 / img.height
    img = img.resize((int(img.width * s), 760), Image.LANCZOS)

p = DST / "chizuru_main.png"
img.save(p)
print("saved", p, img.size)
