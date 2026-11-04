"""从百度图片抓千鹤的图（比必应准），筛选后存到 E:\RentAGirl\out\chizuru_web2"""
import hashlib
import io
import json
import pathlib
import urllib.parse
import urllib.request

from PIL import Image

OUT = pathlib.Path(r"E:\RentAGirl\out\chizuru_web2")
OUT.mkdir(parents=True, exist_ok=True)
UA = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Referer": "https://image.baidu.com/",
}
QUERIES = [
    "水原千鹤 立绘",
    "水原千鹤 全身",
    "水原千鹤 官方",
    "租借女友 千鹤 插画",
    "水原千鹤 和服",
    "水原千鹤 泳装",
    "水原千鹤 微笑",
]


def baidu_images(q, pn=0, rn=30):
    url = ("https://image.baidu.com/search/acjson?tn=resultjson_com&ipn=rj&ct=201326592"
           f"&fp=result&word={urllib.parse.quote(q)}&pn={pn}&rn={rn}")
    d = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=25).read().decode("utf-8", "replace")
    j = json.loads(d)
    out = []
    for it in j.get("data", []):
        if not it:
            continue
        u = it.get("middleURL") or it.get("hoverURL") or it.get("thumbURL")
        if u:
            out.append((u, it.get("width") or 0, it.get("height") or 0))
    return out


def save(url, idx):
    try:
        data = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=20).read()
        if len(data) < 30000:
            return None
        im = Image.open(io.BytesIO(data)).convert("RGB")
        w, h = im.size
        if w < 500:
            return None
        name = hashlib.md5(url.encode()).hexdigest()[:8]
        p = OUT / f"b_{idx:03d}_{name}.png"
        im.save(p)
        return (p, w, h)
    except Exception:
        return None


def main():
    got, idx = 0, 0
    for q in QUERIES:
        try:
            items = baidu_images(q)
        except Exception as e:
            print("搜索失败", q, e)
            continue
        for u, w, h in items:
            if got >= 40:
                break
            r = save(u, idx)
            idx += 1
            if r:
                got += 1
                if got % 10 == 0:
                    print("已保存", got, flush=True)
        if got >= 40:
            break
    print("共保存", got)


if __name__ == "__main__":
    main()
