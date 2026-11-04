"""检测正片结束点（ffmpeg 管道版，比 av 的 seek 可靠）。

本片正片字幕 = 白字 + 粉色描边，固定在底部居中。B站片尾接的别的片段要么没字幕、
要么字幕是别的颜色，用「粉色描边是否还在」当指纹。

用法:
  python detect_cut.py S01E01            # 只打印
  python detect_cut.py S01E01 --write    # 写回 raw\\.meta\\S01E01.json 的 cut_s
  python detect_cut.py S01E01 --debug    # 打印逐 10 秒统计
"""
import argparse, json, pathlib, subprocess, sys
import numpy as np

REPO = pathlib.Path(r"E:\RentAGirl")
CROP = "1000:130:450:945"      # w:h:x:y  底部字幕带
FPS = 2
FRAME_BYTES = 1000 * 130 * 3
PINK_PER_FRAME = 4000          # 单帧粉色像素阈值（约 3% 的字幕带面积）
TAIL_PAD = 3.0


def ffmpeg_exe():
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


def scan(path, scan_from=1000.0):
    cmd = [
        ffmpeg_exe(), "-hide_banner", "-loglevel", "error",
        "-ss", str(int(scan_from)), "-i", str(path),
        "-vf", f"crop={CROP},fps={FPS}",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-",
    ]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, bufsize=FRAME_BYTES * 4)
    t = scan_from
    series = []
    idx = 0
    while True:
        buf = p.stdout.read(FRAME_BYTES)
        if len(buf) < FRAME_BYTES:
            break
        a = np.frombuffer(buf, dtype=np.uint8).reshape(130, 1000, 3).astype(int)
        r, g, b = a[:, :, 0], a[:, :, 1], a[:, :, 2]
        pink = int(((r > 190) & (g < 140) & (b < 180) & (r - g > 60)).sum())
        series.append((t, pink))
        t += 1.0 / FPS
        idx += 1
    p.stdout.close()
    p.wait()
    return series


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ep")
    ap.add_argument("--scan-from", type=float, default=1000.0)
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--debug", action="store_true")
    args = ap.parse_args()

    src = REPO / "raw" / f"{args.ep}.mp4"
    series = scan(src, args.scan_from)
    hits = [t for t, p in series if p >= PINK_PER_FRAME]
    duration = subprocess.run(
        [ffmpeg_exe(), "-hide_banner", "-i", str(src)],
        capture_output=True, text=True, errors="ignore").stderr
    dur = None
    for line in duration.splitlines():
        if "Duration:" in line:
            hh, mm, ss = line.split("Duration:")[1].split(",")[0].strip().split(":")
            dur = int(hh) * 3600 + int(mm) * 60 + float(ss)
            break

    if args.debug:
        for t, p in series[::10]:
            print(f"{t:7.1f}  pink={p:6d}")

    if not hits:
        print(json.dumps({"ep": args.ep, "duration_s": dur, "cut_s": dur,
                          "note": "没检测到粉色字幕，整片保留（需人工确认）"}, ensure_ascii=False))
        return

    last = hits[-1]
    cut = min(dur or last + TAIL_PAD, last + TAIL_PAD)
    res = {"ep": args.ep, "duration_s": dur, "last_pink_sub_s": round(last, 1),
           "cut_s": round(cut, 1), "frames_scanned": len(series),
           "pink_frames": len(hits)}
    print(json.dumps(res, ensure_ascii=False))

    if args.write:
        mp = REPO / "raw" / ".meta" / f"{args.ep}.json"
        meta = json.loads(mp.read_text(encoding="utf-8-sig")) if mp.exists() else {}
        meta["cut_s"] = round(cut, 1)
        meta["cut_detect"] = {"last_pink_sub_s": round(last, 1), "scan_from": args.scan_from}
        mp.write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"meta updated: {mp}")


if __name__ == "__main__":
    main()
