"""做一张投稿封面（1146x717，杂志风）。"""
import pathlib

from PIL import Image, ImageDraw, ImageFilter, ImageFont

OUT = pathlib.Path(r"E:\RentAGirl\out\cover")
OUT.mkdir(parents=True, exist_ok=True)
ART = pathlib.Path(r"E:\RentAGirl\assets_web\web_00.png")
W, H = 1146, 717
CREAM = (246, 241, 231)
INK = (42, 38, 34)
RED = (181, 71, 91)
GRAY = (138, 127, 116)

F_SERIF_B = "C:/Windows/Fonts/msyhbd.ttc"
F_SERIF = "C:/Windows/Fonts/msyh.ttc"
F_MINCHO = "C:/Windows/Fonts/YuMincho.ttc"


def font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", size)


def main():
    im = Image.new("RGB", (W, H), CREAM)
    d = ImageDraw.Draw(im)

    # 右侧照片（带白边）
    art = Image.open(ART).convert("RGB")
    pw, ph = 430, 560
    s = max(pw / art.width, ph / art.height)
    art2 = art.resize((int(art.width * s), int(art.height * s)), Image.LANCZOS)
    left = (art2.width - pw) // 2
    top = int((art2.height - ph) * 0.12)
    art2 = art2.crop((left, top, left + pw, top + ph))

    frame = Image.new("RGB", (pw + 24, ph + 60), (255, 255, 255))
    frame.paste(art2, (12, 12))
    shadow = Image.new("RGB", (frame.width + 40, frame.height + 40), CREAM)
    sd = ImageDraw.Draw(shadow)
    sd.rectangle([20, 26, 20 + frame.width, 26 + frame.height], fill=(222, 214, 200))
    shadow = shadow.filter(ImageFilter.GaussianBlur(9))
    im.paste(shadow, (W - 470, 100))
    im.paste(frame, (W - 480, 90))

    # 左侧文字
    d.text((72, 74), "水 原 千 鶴", font=font(F_MINCHO, 26), fill=RED)
    d.text((74, 112), "MIZUHARA CHIZURU", font=font(F_SERIF, 14), fill=GRAY)
    d.line([(74, 146), (500, 146)], fill=INK, width=2)

    d.text((72, 200), "はじめまして、", font=font(F_MINCHO, 54), fill=INK)
    d.text((72, 268), "千鶴です。", font=font(F_MINCHO, 66), fill=INK)
    d.text((74, 366), "初次见面，我是千鹤。", font=font(F_SERIF_B, 34), fill=INK)

    d.line([(74, 436), (300, 436)], fill=RED, width=4)
    d.text((74, 462), "水原千鶴（一ノ瀬千鶴）自己紹介", font=font(F_SERIF, 20), fill=GRAY)
    d.text((74, 496), "声・絵・編集すべてローカル生成", font=font(F_SERIF, 20), fill=GRAY)
    d.text((74, 600), "RENT-A-GIRLFRIEND｜SHORT FILM", font=font(F_SERIF, 13), fill=GRAY)

    out = OUT / "cover_v1.jpg"
    im.save(out, quality=95)
    print(out, im.size)


if __name__ == "__main__":
    main()
