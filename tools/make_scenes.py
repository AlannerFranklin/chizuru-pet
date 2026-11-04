"""为每句台词生成一张 1920x1080 场景图：模糊插画背景 + 立绘 + 名字牌。
素材轮流用 assets_v3 里的立绘 + 原始插画，做出"有画面切换"的观感。
"""
import pathlib
import random
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageEnhance

W, H = 1920, 1080
ROOT = pathlib.Path(r"E:\RentAGirl")
ART_DIR = ROOT / "assets_v3"
POOL_DIR = ROOT / "assets_card"      # 原始插画的卡片版（有背景）
AI_BG_DIR = ROOT / "out" / "ai_bg"   # ComfyUI 生成的场景图（优先用）
OUT_DIR = ROOT / "out" / "videos" / "scenes"
FONT_B = "C:/Windows/Fonts/msyhbd.ttc"
FONT_R = "C:/Windows/Fonts/msyh.ttc"


def cover(img, w, h):
    s = max(w / img.width, h / img.height)
    im = img.resize((max(1, int(img.width * s)), max(1, int(img.height * s))), Image.LANCZOS)
    left = (im.width - w) // 2
    top = (im.height - h) // 2
    return im.crop((left, top, left + w, top + h))


def make_scene(idx, cutout: Image.Image, bg_src: Image.Image, out_path, ai_bg=False):
    # 背景：铺满 → AI 场景轻压暗；旧插画则模糊压暗
    if ai_bg:
        bg = cover(bg_src.convert("RGB"), W, H)
        bg = ImageEnhance.Brightness(bg).enhance(0.78)
    else:
        bg = cover(bg_src.convert("RGB"), W, H).filter(ImageFilter.GaussianBlur(26))
        bg = ImageEnhance.Brightness(bg).enhance(0.52)
        bg = ImageEnhance.Color(bg).enhance(0.9)

    # 暗角
    vig = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(vig)
    d.ellipse([-W * 0.2, -H * 0.2, W * 1.2, H * 1.2], fill=110)
    vig = vig.filter(ImageFilter.GaussianBlur(200))
    dark = Image.new("RGB", (W, H), (8, 8, 12))
    bg = Image.composite(dark, bg, vig.point(lambda v: int(v * 0.75)))

    # 立绘：高 92%，靠右
    ch = cutout.copy()
    target_h = int(H * 0.92)
    s = target_h / ch.height
    ch = ch.resize((max(1, int(ch.width * s)), target_h), Image.LANCZOS)
    px = int(W * 0.50) + (idx % 3 - 1) * 40
    py = H - ch.height + 24
    bg.paste(ch, (px, py), ch)

    # 左上角压暗，保证名字牌看得清
    top_grad = Image.new("L", (1, 260), 0)  # 名字牌背景
    for y in range(260):
        top_grad.putpixel((0, y), int(170 * (1 - y / 260)))
    top_grad = top_grad.resize((W, 260))
    dark_top = Image.new("RGB", (W, 260), (0, 0, 0))
    bg.paste(Image.composite(dark_top, bg.crop((0, 0, W, 260)), top_grad), (0, 0))

    d = ImageDraw.Draw(bg)
    f_name = ImageFont.truetype(FONT_B, 56)
    f_en = ImageFont.truetype(FONT_R, 25)
    d.text((104, 96), "水原千鶴", font=f_name, fill=(255, 236, 242))
    d.text((108, 172), "Mizuhara Chizuru", font=f_en, fill=(226, 190, 202))
    d.line([(106, 218), (218, 218)], fill=(230, 150, 170), width=4)

    bg.save(out_path)
    return out_path


def build(n, out_prefix="scene"):
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    cutouts = sorted(ART_DIR.glob("*.png")) or [ART_DIR / "chizuru_main.png"]
    ai = sorted(AI_BG_DIR.glob("*.png"))
    pool = sorted(POOL_DIR.glob("*.png"))
    main_cut = cutouts[0]
    cut = Image.open(main_cut).convert("RGBA")
    paths = []
    for i in range(n):
        if ai:
            bg_src = ai[i % len(ai)]
            is_ai = True
        else:
            bg_src = pool[i % len(pool)] if pool else main_cut
            is_ai = False
        p = OUT_DIR / f"{out_prefix}_{i:02d}.png"
        make_scene(i, cut, Image.open(bg_src).convert("RGBA"), p, ai_bg=is_ai)
        paths.append(p)
    return paths


if __name__ == "__main__":
    ps = build(6)
    print("scenes:", [p.name for p in ps])

def make_char_frame(char_path, out_path):
    """把竖版角色图做成 16:9 画面：模糊同图铺底 + 清晰竖图居中 + 底部压暗。"""
    src = Image.open(char_path).convert("RGB")
    W_, H_ = 1920, 1080
    bg = cover(src, W_, H_).filter(ImageFilter.GaussianBlur(30))
    bg = ImageEnhance.Brightness(bg).enhance(0.55)
    bg = ImageEnhance.Color(bg).enhance(0.85)
    fg = src.copy()
    # 原图小的话别硬拉太大，避免糊；放大后补一点锐化
    target_h = min(H_ * 0.98, fg.height * 1.9)
    s = target_h / fg.height
    fg = fg.resize((max(1, int(fg.width * s)), int(target_h)), Image.LANCZOS)
    fg = fg.filter(ImageFilter.UnsharpMask(radius=2, percent=60, threshold=2))
    bg.paste(fg, ((W_ - fg.width) // 2, H_ - fg.height))

    # 底部渐变，压暗让字幕清楚
    grad = Image.new("L", (1, H_), 0)
    for y in range(H_):
        t = max(0.0, (y - H_ * 0.62) / (H_ * 0.38))
        grad.putpixel((0, y), int(150 * min(1.0, t)))
    grad = grad.resize((W_, H_))
    dark = Image.new("RGB", (W_, H_), (0, 0, 0))
    bg = Image.composite(dark, bg, grad)

    # 左上角压暗，保证名字牌看得清
    top_grad = Image.new("L", (1, 260), 0)  # 名字牌背景
    for y in range(260):
        top_grad.putpixel((0, y), int(170 * (1 - y / 260)))
    top_grad = top_grad.resize((W, 260))
    dark_top = Image.new("RGB", (W, 260), (0, 0, 0))
    bg.paste(Image.composite(dark_top, bg.crop((0, 0, W, 260)), top_grad), (0, 0))

    d = ImageDraw.Draw(bg)
    f_name = ImageFont.truetype(FONT_B, 56)
    f_en = ImageFont.truetype(FONT_R, 25)
    d.text((104, 96), "水原千鶴", font=f_name, fill=(255, 236, 242))
    d.text((108, 172), "Mizuhara Chizuru", font=f_en, fill=(226, 190, 202))
    d.line([(106, 218), (218, 218)], fill=(230, 150, 170), width=4)
    bg.save(out_path)
    return out_path
