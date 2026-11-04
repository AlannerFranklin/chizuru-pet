import time, json, pathlib
import numpy as np
import av
from rapidocr import RapidOCR

REPO = pathlib.Path(r"E:\RentAGirl")
CROP = (400, 950, 1520, 1080)
src = REPO / "raw" / "S01E03.mp4"

# 取一帧有字幕的画面
c = av.open(str(src))
vs = c.streams.video[0]
img = None
for f in c.decode(vs):
    t = float(f.pts * vs.time_base) if f.pts else 0
    if t > 600:
        img = f.to_ndarray(format="rgb24")[CROP[1]:CROP[3], CROP[0]:CROP[2], :]
        break
c.close()
print("frame", img.shape)

engine = RapidOCR()
for mode in ("full", "rec_only"):
    t0 = time.time()
    for _ in range(10):
        if mode == "rec_only":
            res = engine(img, use_det=False, use_cls=False, use_rec=True)
        else:
            res = engine(img)
    dt = (time.time() - t0) / 10
    txts = getattr(res, "txts", None)
    print(f"{mode}: {dt*1000:.0f} ms/call  txts={txts}")
