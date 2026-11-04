import pathlib, sys
from rembg import remove, new_session

session = new_session("u2netp")
from PIL import Image

SRC = pathlib.Path(r"E:\dsh\dsh_wechat\媒体")
OUT = pathlib.Path(r"E:\RentAGirl\assets")
OUT.mkdir(parents=True, exist_ok=True)

files = sorted(SRC.glob("*2026-10-28T03-19*.jpg"))
for i, f in enumerate(files, 1):
    img = Image.open(f)
    cut = remove(img, session=session)
    dst = OUT / f"chizuru_{i:02d}.png"
    cut.save(dst)
    print(dst.name, cut.size)
