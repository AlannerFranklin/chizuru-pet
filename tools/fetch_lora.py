"""专门抓《租借女友》动画截图/官方图的千鹤素材。"""
import hashlib
import io
import json
import pathlib
import urllib.parse
import urllib.request

from PIL import Image

OUT = pathlib.Path(r"E:\RentAGirl\lora_data\raw")
OUT.mkdir(parents=True, exist_ok=True)
UA = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Referer": "https://image.baidu.com/",
}
QUERIES = [
    "租借女友 动画截图 千鹤",
    "水原千鹤 动画截图",
    "水原千鹤 动画 第2季",
    "水原千鹤 动画 表情",
    "kanojo okarishimasu chizuru anime screenshot",
    "租借女友 千鹤 官方 设定",
    "水原千鹤 动画 脸",
    "水原千鹤 动画 和服",
    "水原千鹤 动画 微笑",
    "水原千鹤 动画 哭",
    "租借女友 千鹤 动画 全身",
    "水原千鹤 动画 侧脸",
    "水原千鹤 官方壁纸",
    "水原千鹤 动画 校服",
]


def baidu(q, pn=0, rn=30):
    url = ("https://image.baidu.com/search/acjson?tn=resultjson_com&ipn=rj&ct=201326592"
           f"&fp=result&word={urllib.parse.quote(q)}&pn={pn}&rn={rn}")
    d = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=25).read().decode("utf-8", "replace")
    j = json.loads(d)
    out = []
    for it in j.get("data", []):
        if not it:
            continue
        u = it.get("middleURL") or it.get("hoverURL")
        if u:
            out.append(u)
    return out


def save(url):
    try:
        data = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=20).read()
        if len(data) < 25000:
            return None
        im = Image.open(io.BytesIO(data)).convert("RGB")
        w, h = im.size
        if min(w, h) < 400:
            return None
        digest = hashlib.md5(im.resize((64, 64)).tobytes()).hexdigest()[:10]
        p = OUT / f"{digest}.png"
        if p.exists():
            return None
        im.save(p)
        return (p, w, h)
    except Exception:
        return None


def main():
    total = 0
    for q in QUERIES:
        for pn in (0, 30):
            try:
                urls = baidu(q, pn)
            except Exception as e:
                print("搜索失败", q, e)
                continue
            for u in urls:
                r = save(u)
                if r:
                    total += 1
            print(f"{q} pn={pn}: 累计 {total}", flush=True)
            if total >= 160:
                break
        if total >= 160:
            break
    print("总数", total)


if __name__ == "__main__":
    main()
