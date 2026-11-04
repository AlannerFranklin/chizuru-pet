"""给已有抠图补内部透明洞（手部/发丝等被误删的区域）。"""
import pathlib
import numpy as np
from PIL import Image
from scipy import ndimage

SRC = pathlib.Path(r"E:\RentAGirl\assets")
DST = pathlib.Path(r"E:\RentAGirl\assets_v2")
DST.mkdir(parents=True, exist_ok=True)

for f in sorted(SRC.glob("chizuru_*.png")):
    im = Image.open(f).convert("RGBA")
    arr = np.array(im)
    a = arr[:, :, 3]
    solid = a > 60
    # 闭运算把细缝连上，再填内部洞
    closed = ndimage.binary_closing(solid, structure=np.ones((7, 7)))
    filled = ndimage.binary_fill_holes(closed)
    add = filled & ~solid
    arr[:, :, 3] = np.where(add, 255, a).astype(np.uint8)
    Image.fromarray(arr).save(DST / f.name)
    print(f.name, "filled pixels", int(add.sum()))
