"""批量抓候选图（目标 1000+），只做基础过滤（尺寸/色彩/去重），不做人工判断。"""
import hashlib
import io
import json
import pathlib
import urllib.parse
import urllib.request

from PIL import Image

OUT = pathlib.Path(r"E:\RentAGirl\review_img\candidates")
OUT.mkdir(parents=True, exist_ok=True)
UA = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Referer": "https://image.baidu.com/",
}
QUERIES = [
    "水原千鹤", "租借女友 千鹤", "水原千鹤 立绘", "水原千鹤 全身", "水原千鹤 官方",
    "水原千鹤 动画截图", "水原千鹤 校服", "水原千鹤 便服", "水原千鹤 浴衣",
    "水原千鹤 泳装", "水原千鹤 微笑", "水原千鹤 表情", "水原千鹤 头像",
    "水原千鹤 壁纸", "水原千鹤 生日", "水原千鹤 约会", "水原千鹤 制服",
    "租借女友 动画 高清", "租借女友 千鹤 全身立绘", "租借女友 千鹤 官方图",
    "mizuhara chizuru", "chizuru mizuhara full body", "chizuru mizuhara official",
    "kanojo okarishimasu chizuru", "千鹤 租借女友 插画", "水原千鹤 半身",
    "水原千鹤 站姿", "水原千鹤 侧身", "水原千鹤 特写", "水原千鹤 高清壁纸",
]


def baidu(q, pn):
    url = ("https://image.baidu.com/search/acjson?tn=resultjson_com&ipn=rj&ct=201326592"
           f"&fp=result&word={urllib.parse.quote(q)}&pn={pn}&rn=30")
    d = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=25).read().decode("utf-8", "replace")
    out = []
    for it in json.loads(d).get("data", []):
        if not it:
            continue
        u = it.get("middleURL") or it.get("hoverURL")
        if u:
            out.append(u)
    return out


def save(url):
    try:
        data = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=20).read()
        if len(data) < 20000:
            return None
        im = Image.open(io.BytesIO(data)).convert("RGB")
        w, h = im.size
        if min(w, h) < 400:
            return None
        d = hashlib.md5(im.resize((40, 40)).tobytes()).hexdigest()[:14]
        p = OUT / f"{d}.jpg"
        if p.exists():
            return None
        im.save(p, quality=92)
        return p
    except Exception:
        return None


def main():
    got = 0
    target = 1100
    for q in QUERIES:
        for pn in (0, 30, 60, 90, 120):
            if got >= target:
                break
            try:
                urls = baidu(q, pn)
            except Exception:
                continue
            if not urls:
                break
            for u in urls:
                if save(u):
                    got += 1
            print(f"{q} pn={pn} -> {got}", flush=True)
        if got >= target:
            break
    print("TOTAL", got)


if __name__ == "__main__":
    main()
