"""用 isnet-anime 模型重新抠图（更适合二次元），并填补内部小洞。"""
import pathlib
import numpy as np
from PIL import Image
from rembg import remove, new_session
from scipy import ndimage

SRC = pathlib.Path(r"E:\dsh\dsh_wechat\媒体")
OUT = pathlib.Path(r"E:\RentAGirl\assets_v2")
OUT.mkdir(parents=True, exist_ok=True)

session = new_session("isnet-anime")
files = sorted(SRC.glob("*2026-10-28T03-19*.jpg"))

for i, f in enumerate(files, 1):
    img = Image.open(f).convert("RGB")
    cut = remove(img, session=session).convert("RGBA")
    arr = np.array(cut)
    alpha = arr[:, :, 3]
    # 填补内部小洞：先把透明区域做闭运算
    mask = alpha > 40
    filled = ndimage.binary_closing(mask, structure=np.ones((9, 9)))
    filled = ndimage.binary_fill_holes(filled)
    # 只填补"被包围"的洞，不扩到外部
    new_alpha = np.where(filled & ~mask, 255, alpha).astype(np.uint8)
    arr[:, :, 3] = new_alpha
    dst = OUT / f"chizuru_{i:02d}.png"
    Image.fromarray(arr).save(dst)
    holes = 0
    for y in range(0, new_alpha.shape[0], 4):
        row = new_alpha[y]
        idx = np.where(row > 200)[0]
        if idx.size < 2:
            continue
        holes += int(np.sum(row[idx[0]:idx[-1]] < 30))
    print(dst.name, "holes", holes)
