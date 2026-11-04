"""快速版：并行 + JPEG draft 降采样解码，扫描全部素材并分级。"""
import hashlib
import json
import pathlib
from concurrent.futures import ProcessPoolExecutor

import numpy as np
from PIL import Image, ImageFilter, ImageStat

ROOT = pathlib.Path(r"D:\download\梦C041【水原千鹤】\梦C041【水原千鹤】\梦C041【水原千鹤】")
OUT = pathlib.Path(r"E:\RentAGirl\lora_data\pack_clean")
OUT.mkdir(parents=True, exist_ok=True)
META = pathlib.Path(r"E:\RentAGirl\lora_data\pack_meta.jsonl")
PROG = pathlib.Path(r"E:\RentAGirl\lora_data\scan_progress.txt")


def skin(arr):
    r = arr[:, :, 0].astype(np.int16)
    g = arr[:, :, 1].astype(np.int16)
    b = arr[:, :, 2].astype(np.int16)
    m = (r > 95) & (g > 40) & (b > 20) & (r > g + 15) & (r > b + 15) & (np.abs(r - g) > 10)
    return float(m.mean())


def one(path_str):
    p = pathlib.Path(path_str)
    try:
        im = Image.open(p)
        w, h = im.size
        if min(w, h) < 640:
            return None
        if p.suffix.lower() in (".jpg", ".jpeg"):
            im.draft("RGB", (256, 256))       # JPEG 快速降采样
        im = im.convert("RGB")
        small = im.resize((64, 64))
        key = hashlib.md5(small.tobytes()).hexdigest()
        arr = np.asarray(im.resize((96, 96)))
        whole = skin(arr)
        torso = skin(arr[24:84, 24:72])
        g = im.convert("L")
        sharp = float(ImageStat.Stat(g.filter(ImageFilter.FIND_EDGES)).var[0])
        sat = float(ImageStat.Stat(im.convert("HSV")).mean[1])
        return {"p": str(p), "k": key, "w": w, "h": h, "whole": round(whole, 3),
                "torso": round(torso, 3), "sharp": round(sharp, 1), "sat": round(sat, 1)}
    except Exception:
        return None


def main():
    files = [str(p) for p in ROOT.rglob("*") if p.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp")]
    print("总文件", len(files), flush=True)
    rows, done = [], 0
    with ProcessPoolExecutor(max_workers=8) as ex:
        for r in ex.map(one, files, chunksize=32):
            done += 1
            if done % 500 == 0:
                PROG.write_text(f"{done}/{len(files)}", encoding="utf-8")
                print(f"{done}/{len(files)}", flush=True)
            if r:
                rows.append(r)
    print("有效", len(rows), flush=True)

    seen, uniq = set(), []
    for r in rows:
        if r["k"] in seen:
            continue
        seen.add(r["k"])
        uniq.append(r)
    print("去重后", len(uniq), flush=True)

    safe = [r for r in uniq if r["whole"] < 0.10 and r["torso"] < 0.28 and r["sat"] > 18]
    safe.sort(key=lambda r: -r["sharp"])
    print("正常穿着候选", len(safe), flush=True)

    for r in safe:
        src = pathlib.Path(r["p"])
        dst = OUT / (hashlib.md5(str(src).encode()).hexdigest()[:12] + ".jpg")
        if not dst.exists():
            try:
                Image.open(src).convert("RGB").save(dst, quality=93)
            except Exception:
                pass
    META.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in uniq), encoding="utf-8")
    print("完成", flush=True)


if __name__ == "__main__":
    main()
