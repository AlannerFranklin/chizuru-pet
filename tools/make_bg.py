"""用 PIL 画视频背景（含名字与标题），避免 ffmpeg drawtext 的中文字体问题。"""
import pathlib
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1920, 1080
FONT_B = "C:/Windows/Fonts/msyhbd.ttc"
FONT_R = "C:/Windows/Fonts/msyh.ttc"


def make_bg(title="", out=None):
    img = Image.new("RGB", (W, H), (24, 20, 26))
    d = ImageDraw.Draw(img)
    top, bot = (54, 34, 44), (14, 12, 18)
    for y in range(H):
        t = y / (H - 1)
        d.line([(0, y), (W, y)],
               fill=(int(top[0] * (1 - t) + bot[0] * t),
                     int(top[1] * (1 - t) + bot[1] * t),
                     int(top[2] * (1 - t) + bot[2] * t)))

    glow = Image.new("RGB", (W, H), (0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse([W * 0.58, -H * 0.3, W * 1.1, H * 0.7], fill=(120, 56, 70))
    glow = glow.filter(ImageFilter.GaussianBlur(180))
    img = Image.blend(img, glow, 0.42)

    d = ImageDraw.Draw(img)
    f_name = ImageFont.truetype(FONT_B, 58)
    f_en = ImageFont.truetype(FONT_R, 26)
    f_title = ImageFont.truetype(FONT_R, 32)
    d.text((108, 104), "水原千鶴", font=f_name, fill=(255, 233, 240))
    d.text((112, 182), "Mizuhara Chizuru", font=f_en, fill=(224, 184, 196))
    if title:
        d.text((112, H - 196), title, font=f_title, fill=(214, 200, 208))

    # 左下淡色装饰线
    d.line([(112, H - 226), (112 + 120, H - 226)], fill=(230, 150, 170), width=4)

    out = pathlib.Path(out) if out else pathlib.Path(r"E:\RentAGirl\out\videos\bg.png")
    img.save(out)
    return out


if __name__ == "__main__":
    print(make_bg("はじめまして、水原千鶴です"))

def make_intro(name, sub, out=None):
    """片头卡：深色渐变 + 大标题 + 一行副标题。"""
    img = Image.new("RGB", (W, H), (12, 10, 14))
    d = ImageDraw.Draw(img)
    for y in range(H):
        t = y / (H - 1)
        d.line([(0, y), (W, y)], fill=(int(40 * (1 - t) + 10 * t),
                                       int(26 * (1 - t) + 8 * t),
                                       int(34 * (1 - t) + 12 * t)))
    glow = Image.new("RGB", (W, H), (0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse([W * 0.2, H * 0.25, W * 0.8, H * 0.85], fill=(140, 62, 80))
    glow = glow.filter(ImageFilter.GaussianBlur(200))
    img = Image.blend(img, glow, 0.45)

    d = ImageDraw.Draw(img)
    f1 = ImageFont.truetype(FONT_B, 120)
    f2 = ImageFont.truetype(FONT_R, 40)
    w1 = d.textlength(name, font=f1)
    w2 = d.textlength(sub, font=f2)
    d.text(((W - w1) / 2, H * 0.40), name, font=f1, fill=(255, 240, 245))
    d.text(((W - w2) / 2, H * 0.58), sub, font=f2, fill=(226, 186, 200))
    d.line([(W / 2 - 90, H * 0.70), (W / 2 + 90, H * 0.70)], fill=(230, 150, 170), width=4)

    out = pathlib.Path(out) if out else pathlib.Path(r"E:\RentAGirl\out\videos\intro.png")
    img.save(out)
    return out