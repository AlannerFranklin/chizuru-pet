"""补内部洞：用最近的『不透明角色像素』的颜色填充，避免把背景补进来。"""
import pathlib
import numpy as np
from PIL import Image
from scipy import ndimage

SRC = pathlib.Path(r"E:\RentAGirl\assets")
DST = pathlib.Path(r"E:\RentAGirl\assets_v2")
DST.mkdir(parents=True, exist_ok=True)

for png in sorted(SRC.glob("chizuru_*.png")):
    cut = Image.open(png).convert("RGBA")
    arr = np.array(cut)
    a = arr[:, :, 3]
    solid = a > 60

    closed = ndimage.binary_closing(solid, structure=np.ones((5, 5)))
    filled = ndimage.binary_fill_holes(closed)
    add = filled & ~solid

    # 用最近的实心像素颜色填充
    idx = ndimage.distance_transform_edt(~solid, return_distances=False, return_indices=True)
    nearest = arr[idx[0], idx[1], :3]
    out = arr.copy()
    out[add, :3] = nearest[add]
    out[add, 3] = 255

    # 只填补面积小于 8000 像素的洞（大块是背景，不该补）
    lab, n = ndimage.label(add)
    for i in range(1, n + 1):
        m = lab == i
        if m.sum() > 8000:
            out[m] = arr[m]
    Image.fromarray(out).save(DST / png.name)
    print(png.name, "filled", int(add.sum()))
