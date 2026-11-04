import re
import urllib.parse
import urllib.request

UA = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}


def _clean(s):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", s or "")).strip()


def search(q, n=6):
    url = "https://www.bing.com/search?q=" + urllib.parse.quote(q) + "&mkt=zh-CN"
    out = []
    try:
        html = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=20).read().decode("utf-8", "replace")
        for block in re.split(r'<li class="b_algo', html)[1:]:
            block = block[:5000]
            a = re.search(r'<h2[^>]*>\s*<a[^>]+href="(https?://[^"]+)"[^>]*>(.*?)</a>', block, re.S)
            if not a:
                a = re.search(r'<a[^>]+href="(https?://[^"]+)"[^>]*>(.*?)</a>', block, re.S)
            if not a:
                continue
            title = _clean(a.group(2))
            if not title:
                continue
            p = re.search(r"<p[^>]*>(.*?)</p>", block, re.S)
            out.append((title, a.group(1), _clean(p.group(1)) if p else ""))
            if len(out) >= n:
                break
    except Exception as e:
        print("search err", e)
    return out


def fetch(url, limit=3000):
    req = urllib.request.Request(url, headers=UA)
    html = urllib.request.urlopen(req, timeout=25).read().decode("utf-8", "replace")
    html = re.sub(r"(?is)<(script|style|noscript).*?</\1>", " ", html)
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html)).strip()[:limit]


if __name__ == "__main__":
    import sys
    q = sys.argv[1] if len(sys.argv) > 1 else "水原千鶴"
    for t, u, s in search(q):
        print("-", t[:60], "|", u[:70])
        print("  ", s[:100])
