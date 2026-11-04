"""补洞时用原图 RGB（避免黑洞），alpha 来自抠图结果。"""
import pathlib
import numpy as np
from PIL import Image
from scipy import ndimage

SRC_JPG = pathlib.Path(r"E:\dsh\dsh_wechat\媒体")
SRC_A = pathlib.Path(r"E:\RentAGirl\assets")
DST = pathlib.Path(r"E:\RentAGirl\assets_v2")
DST.mkdir(parents=True, exist_ok=True)

jpgs = sorted(SRC_JPG.glob("*2026-10-28T03-19*.jpg"))
pngs = sorted(SRC_A.glob("chizuru_*.png"))

for jpg, png in zip(jpgs, pngs):
    rgb = Image.open(jpg).convert("RGB")
    cut = Image.open(png).convert("RGBA")
    if rgb.size != cut.size:
        rgb = rgb.resize(cut.size, Image.LANCZOS)
    r = np.array(rgb)
    arr = np.array(cut)
    a = arr[:, :, 3]

    solid = a > 60
    closed = ndimage.binary_closing(solid, structure=np.ones((7, 7)))
    filled = ndimage.binary_fill_holes(closed)
    add = filled & ~solid

    out = np.dstack([r, a])
    out[add, 3] = 255
    Image.fromarray(out).save(DST / png.name)
    print(png.name, "filled", int(add.sum()))
