"""大量抓取千鹤图（百度图片），多关键词 + 翻页，去重后存 raw2。"""
import hashlib
import io
import json
import pathlib
import urllib.parse
import urllib.request

from PIL import Image

OUT = pathlib.Path(r"E:\RentAGirl\lora_data\raw2")
OUT.mkdir(parents=True, exist_ok=True)
UA = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Referer": "https://image.baidu.com/",
}
QUERIES = [
    "租借女友 水原千鹤 动画截图",
    "水原千鹤 全身 立绘",
    "水原千鹤 官方 插画",
    "水原千鹤 动画 高清",
    "水原千鹤 校服 全身",
    "水原千鹤 浴衣 全身",
    "水原千鹤 泳装 全身",
    "水原千鹤 微笑 正面",
    "水原千鹤 侧脸",
    "水原千鹤 哭 表情",
    "水原千鹤 生气 表情",
    "kanojo okarishimasu chizuru full body",
    "chizuru mizuhara official art",
    "租借女友 千鹤 第二季 截图",
    "租借女友 千鹤 第三季",
    "水原千鹤 约会 场景",
    "水原千鹤 和服 正面",
    "水原千鹤 半身像",
    "水原千鹤 key visual",
    "水原千鹤 生诞祭",
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


def save(url, idx):
    try:
        data = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=20).read()
        if len(data) < 25000:
            return None
        im = Image.open(io.BytesIO(data)).convert("RGB")
        w, h = im.size
        if min(w, h) < 480:
            return None
        d = hashlib.md5(im.resize((48, 48)).tobytes()).hexdigest()[:12]
        p = OUT / f"{d}.png"
        if p.exists():
            return None
        im.save(p)
        return p
    except Exception:
        return None


def main():
    got = 0
    for q in QUERIES:
        for pn in (0, 30, 60, 90):
            try:
                urls = baidu(q, pn)
            except Exception as e:
                print("fail", q, pn, e)
                continue
            for u in urls:
                if save(u, got):
                    got += 1
            print(f"{q} pn={pn} -> 累计 {got}", flush=True)
            if got >= 560:
                break
        if got >= 560:
            break
    print("总数", got)


if __name__ == "__main__":
    main()
