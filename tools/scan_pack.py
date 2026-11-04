"""扫描全部素材：去重、质量打分、按暴露程度分级，挑出"正常穿着"的候选。"""
import hashlib
import json
import pathlib
import shutil

import numpy as np
from PIL import Image, ImageFilter, ImageStat

ROOT = pathlib.Path(r"D:\download\梦C041【水原千鹤】\梦C041【水原千鹤】\梦C041【水原千鹤】")
OUT = pathlib.Path(r"E:\RentAGirl\lora_data\pack_clean")
OUT.mkdir(parents=True, exist_ok=True)
META = pathlib.Path(r"E:\RentAGirl\lora_data\pack_meta.jsonl")


def skin(arr):
    r = arr[:, :, 0].astype(np.int16)
    g = arr[:, :, 1].astype(np.int16)
    b = arr[:, :, 2].astype(np.int16)
    m = (r > 95) & (g > 40) & (b > 20) & (r > g + 15) & (r > b + 15) & (np.abs(r - g) > 10)
    return float(m.mean())


def main():
    files = [p for p in ROOT.rglob("*") if p.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp")]
    print("总文件", len(files), flush=True)
    seen = set()
    kept = 0
    rows = []
    for i, p in enumerate(files):
        try:
            im = Image.open(p).convert("RGB")
        except Exception:
            continue
        w, h = im.size
        if min(w, h) < 640:
            continue
        small = im.resize((64, 64))
        key = hashlib.md5(small.tobytes()).hexdigest()
        if key in seen:
            continue
        seen.add(key)

        # 中央区域（躯干）与整体肤色占比
        arr = np.asarray(im.resize((96, 96)))
        whole = skin(arr)
        cx0, cx1 = 24, 72
        cy0, cy1 = 24, 84
        torso = skin(arr[cy0:cy1, cx0:cx1])

        g = im.convert("L").resize((256, 256))
        sharp = float(ImageStat.Stat(g.filter(ImageFilter.FIND_EDGES)).var[0])
        sat = float(ImageStat.Stat(im.convert("HSV")).mean[1])

        rows.append({"p": str(p), "w": w, "h": h, "whole": round(whole, 3),
                     "torso": round(torso, 3), "sharp": round(sharp, 1), "sat": round(sat, 1)})
        if i % 1000 == 0:
            print(f"  {i}/{len(files)} 已处理", flush=True)

    META.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows), encoding="utf-8")
    print("去重后", len(rows), flush=True)

    # 分级：正常穿着
    safe = [r for r in rows if r["whole"] < 0.10 and r["torso"] < 0.28 and r["sat"] > 18]
    safe.sort(key=lambda r: -r["sharp"])
    print("正常穿着候选:", len(safe), flush=True)
    for r in safe:
        src = pathlib.Path(r["p"])
        dst = OUT / (hashlib.md5(str(src).encode()).hexdigest()[:12] + ".jpg")
        if not dst.exists():
            Image.open(src).convert("RGB").save(dst, quality=93)
    print("已复制到", OUT, flush=True)


if __name__ == "__main__":
    main()
