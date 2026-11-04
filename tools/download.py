"""批量下载 B 站合集分P，按季/集编号存进 raw\\。
用法:
  python download.py --dry-run            # 只看选中哪些
  python download.py --items 1-12         # 下第一季
  python download.py --items 1-51         # 全下
说明:
  - 不带 cookie，最高 1080P（4K/60帧 是大会员限定，属于 B 站正常限制，不绕过）
  - 每集单独调用 yt-dlp，已存在就跳过，中断可续
  - 下完写 raw\\.meta\\SxxEyy.json（含 cut_s=1470，片尾过审片段裁掉）
"""
import argparse, json, pathlib, subprocess, sys, time

REPO = pathlib.Path(r"E:\RentAGirl")
RAW = REPO / "raw"
INCOMING = REPO / "incoming"
META = RAW / ".meta"
BV = "BV1ewojBLEyD"
URL = f"https://www.bilibili.com/video/{BV}/"

# 合集 51 个分P 的季/集映射（如与实际不符，改这里）
SEASON_MAP = [
    {"season": 1, "from": 1,  "to": 12},
    {"season": 2, "from": 13, "to": 24},
    {"season": 3, "from": 25, "to": 36},
    {"season": 4, "from": 37, "to": 48},
    {"season": 5, "from": 49, "to": 61},
]
FORMAT = "bv[height<=1080][vcodec^=avc1]+ba[acodec^=mp4a]/bv[height<=1080]+ba/b"
FFMPEG = None


def season_ep(p):
    for m in SEASON_MAP:
        if m["from"] <= p <= m["to"]:
            return m["season"], p - m["from"] + 1
    return 0, p


def parse_items(spec, total=51):
    if spec == "all":
        return list(range(1, total + 1))
    out = []
    for part in spec.split(","):
        part = part.strip()
        if "-" in part:
            a, b = part.split("-")
            out.extend(range(int(a), int(b) + 1))
        elif part:
            out.append(int(part))
    return sorted(set(x for x in out if 1 <= x <= total))


def main():
    global FFMPEG
    import imageio_ffmpeg
    FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()

    ap = argparse.ArgumentParser()
    ap.add_argument("--items", default="all")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--limit-rate", default="8M")
    args = ap.parse_args()

    RAW.mkdir(parents=True, exist_ok=True)
    META.mkdir(parents=True, exist_ok=True)
    INCOMING.mkdir(parents=True, exist_ok=True)

    items = parse_items(args.items)
    plan = []
    for p in items:
        s, e = season_ep(p)
        target = RAW / f"S{s:02d}E{e:02d}.mp4"
        plan.append((p, s, e, target))

    if args.dry_run:
        for p, s, e, t in plan:
            print(f"P{p:02d} -> S{s:02d}E{e:02d}  {'[已存在]' if t.exists() else ''}")
        return

    todo = [(p, s, e, t) for p, s, e, t in plan if not t.exists()]
    print(f"计划 {len(plan)} 集，已有 {len(plan)-len(todo)} 集，待下 {len(todo)} 集", flush=True)

    for i, (p, s, e, target) in enumerate(todo, 1):
        url = f"{URL}?p={p}"
        out_tmpl = str(RAW / f"S{s:02d}E{e:02d}.%(ext)s")
        cmd = [
            sys.executable, "-m", "yt_dlp",
            "--no-warnings", "--newline",
            "-f", FORMAT,
            "--merge-output-format", "mp4",
            "--ffmpeg-location", FFMPEG,
            "--limit-rate", args.limit_rate,
            "--retries", "5", "--fragment-retries", "5",
            "--continue",
            "-o", out_tmpl,
            url,
        ]
        print(f"\n=== [{i}/{len(todo)}] P{p} -> {target.name} ===", flush=True)
        t0 = time.time()
        rc = subprocess.call(cmd)
        if rc != 0:
            print(f"!! P{p} 下载失败 rc={rc}", flush=True)
            continue
        meta = {
            "page": p, "season": s, "episode": e,
            "url": url, "downloaded_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "cut_s": 1470,
            "note": "B站片尾过审片段，默认 24:30 处裁掉；如正片更长请改 cut_s",
        }
        (META / f"S{s:02d}E{e:02d}.json").write_text(
            json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"OK P{p} -> {target.name}  ({time.time()-t0:.0f}s)", flush=True)

    print("\n全部完成。下一步: python process_episode.py S01E02 ...", flush=True)


if __name__ == "__main__":
    main()
