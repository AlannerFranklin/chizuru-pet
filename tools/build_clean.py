"""按人工挑选的索引组装干净数据集：
- clean_face/ 512 脸部偏重裁切（训练身份用）
- clean_full/ 全身图（保留，用于全身生成参考）
"""
import hashlib
import pathlib
import shutil

from PIL import Image

ROOT = pathlib.Path(r"E:\RentAGirl\lora_data")
CAND = (ROOT / "clean_candidates.txt").read_text(encoding="utf-8").splitlines()

# 人工从拼图上挑出来的（sheet 0 / 1 / 2 的编号）
PICKS = [
    # sheet 0
    12, 14, 21, 23, 31, 37, 41, 49, 50, 52, 53, 56, 57, 58,
    # sheet 1
    60, 61, 62, 63, 64, 69, 71, 72, 73, 75, 77, 81, 82, 83, 84, 85, 86, 87, 88, 89,
    90, 91, 93, 94, 97, 98, 100, 101, 104, 105, 109, 110, 111, 113, 114, 115, 116, 117,
]

FACE = ROOT / "clean_face"
FULL = ROOT / "clean_full"
for d in (FACE, FULL):
    d.mkdir(exist_ok=True)
    for f in d.glob("*"):
        f.unlink()

KEY = "chizuru, anime screenshot, 1girl, brown hair, brown eyes"


def add(im, name):
    w, h = im.size
    # 脸部裁切：上半部方形
    side = min(w, int(h * 0.9))
    left = (w - side) // 2
    top = 0 if h <= side else int((h - side) * 0.08)
    face = im.crop((left, top, left + side, top + side)).resize((512, 512), Image.LANCZOS)
    face.save(FACE / f"{name}.png")
    (FACE / f"{name}.txt").write_text(KEY + ", upper body", encoding="utf-8")
    # 全身：仅当原图是竖构图
    if h >= w * 1.25:
        full = im.resize((512, int(512 * h / w)), Image.LANCZOS)
        full.save(FULL / f"{name}.png")


def main():
    n = 0
    used = set()
    # 1) 先收之前已验证过的 raw（按内容 hash 去重）
    for src in sorted((ROOT / "raw").glob("*.png")):
        im = Image.open(src).convert("RGB")
        key = hashlib.md5(im.resize((48, 48)).tobytes()).hexdigest()
        if key in used:
            continue
        used.add(key)
        add(im, f"r{n:04d}")
        n += 1
    print("raw 全部:", n)

    # 2) 人工挑选的
    picked = 0
    for idx in PICKS:
        if idx >= len(CAND):
            continue
        p = pathlib.Path(CAND[idx])
        try:
            im = Image.open(p).convert("RGB")
        except Exception:
            continue
        key = hashlib.md5(im.resize((48, 48)).tobytes()).hexdigest()
        if key in used:
            continue
        used.add(key)
        add(im, f"p{picked:04d}")
        picked += 1
    print("额外挑选:", picked)
    print("clean_face:", len(list(FACE.glob('*.png'))), "clean_full:", len(list(FULL.glob('*.png'))))


if __name__ == "__main__":
    main()
