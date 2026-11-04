"""合并 raw + raw2，去重、按质量排序，生成精选列表和拼图预览。"""
import hashlib
import pathlib

from PIL import Image, ImageFilter, ImageStat

ROOT = pathlib.Path(r"E:\RentAGirl\lora_data")
OUT = ROOT / "pool"
OUT.mkdir(exist_ok=True)


def quality(p):
    im = Image.open(p).convert("RGB")
    w, h = im.size
    sat = ImageStat.Stat(im.convert("HSV")).mean[1]
    g = im.convert("L").resize((256, 256))
    sharp = ImageStat.Stat(g.filter(ImageFilter.FIND_EDGES)).var[0]
    return {"p": p, "w": w, "h": h, "sat": sat, "sharp": sharp,
            "score": sharp * (min(w, h) / 512) ** 0.5}


def main():
    seen = {}
    for d in (ROOT / "raw", ROOT / "raw2"):
        if not d.exists():
            continue
        for p in sorted(d.glob("*.png")):
            try:
                im = Image.open(p).convert("RGB")
            except Exception:
                continue
            key = hashlib.md5(im.resize((48, 48)).tobytes()).hexdigest()
            if key in seen:
                continue
            seen[key] = p
    print("去重后:", len(seen))

    rows = []
    for p in seen.values():
        try:
            q = quality(p)
        except Exception:
            continue
        if q["sat"] < 18 or min(q["w"], q["h"]) < 460 or q["sharp"] < 18:
            continue
        rows.append(q)
    rows.sort(key=lambda r: -r["score"])
    print("通过基础筛选:", len(rows))

    keep = rows[:280]
    (ROOT / "pool_list.txt").write_text("\n".join(str(r["p"]) for r in keep), encoding="utf-8")

    from PIL import ImageDraw, ImageFont
    f = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", 18)
    per = 60
    for page in range(0, len(keep), per):
        chunk = keep[page:page + per]
        cols, cell = 10, 190
        rowsn = (len(chunk) + cols - 1) // cols
        sheet = Image.new("RGB", (cols * cell, rowsn * cell), (24, 24, 24))
        d = ImageDraw.Draw(sheet)
        for i, r in enumerate(chunk):
            im = Image.open(r["p"]).convert("RGB")
            im.thumbnail((cell - 6, cell - 6))
            x = (i % cols) * cell + (cell - im.width) // 2
            y = (i // cols) * cell + (cell - im.height) // 2
            sheet.paste(im, (x, y))
            d.rectangle([(i % cols) * cell, (i // cols) * cell,
                         (i % cols) * cell + 40, (i // cols) * cell + 22], fill=(0, 0, 0))
            d.text(((i % cols) * cell + 3, (i // cols) * cell + 2), str(page + i), font=f,
                   fill=(255, 220, 120))
        out = ROOT / f"pool_sheet_{page // per}.jpg"
        sheet.save(out, quality=84)
        print(out)


if __name__ == "__main__":
    main()
