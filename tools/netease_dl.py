"""网易云下载 BGM：优先挑免费曲，下载后校验时长。"""
import json
import pathlib
import subprocess
import urllib.parse
import urllib.request

OUT = pathlib.Path(r"E:\RentAGirl\bgm")
OUT.mkdir(parents=True, exist_ok=True)
FFPROBE = r"E:\RentAGirl\bin\ffprobe.exe"
UA = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36",
    "Referer": "https://music.163.com/",
}
QUERIES = [
    "merry christmas mr lawrence piano",
    "river flows in you",
    "kiss the rain",
    "summer 久石让 piano",
    "always with me 千与千寻 piano",
    "canon in d piano",
    "天空之城 钢琴",
    "luv letter",
]


def search(q, n=8):
    url = ("https://music.163.com/api/search/get/web?s=" + urllib.parse.quote(q)
           + f"&type=1&limit={n}&offset=0")
    d = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=15).read().decode("utf-8", "replace")
    return json.loads(d).get("result", {}).get("songs", []) or []


def duration(path):
    try:
        r = subprocess.run([FFPROBE, "-v", "error", "-show_entries", "format=duration",
                            "-of", "default=nw=1:nk=1", str(path)],
                           capture_output=True, text=True, timeout=20)
        return float((r.stdout or "0").strip() or 0)
    except Exception:
        return 0.0


def try_download(song_id, path):
    url = f"https://music.163.com/song/media/outer/url?id={song_id}.mp3"
    try:
        data = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40).read()
    except Exception as e:
        return None, f"下载失败 {type(e).__name__}"
    path.write_bytes(data)
    d = duration(path)
    if d < 30:
        path.unlink(missing_ok=True)
        return None, f"无效({len(data)//1024}KB, {d:.1f}s)"
    return path, f"{d:.0f}s {len(data)//1024}KB"


def main():
    for q in QUERIES:
        try:
            songs = search(q)
        except Exception as e:
            print("搜索失败", q, e)
            continue
        print(f"Q: {q} -> {len(songs)} 首")
        for s in songs[:5]:
            name = s.get("name", "")
            artist = ",".join(a.get("name", "") for a in s.get("artists", []))
            safe = "".join(c for c in name if c not in '\\/:*?"<>|')[:36] or "bgm"
            p = OUT / f"{safe}.mp3"
            got, msg = try_download(s.get("id"), p)
            print(f"   {name} - {artist}: {msg}")
            if got:
                print("OK:", got)
                return
    print("没找到能直接下的免费曲")


if __name__ == "__main__":
    main()
