"""她自己的短视频 v2：更讲究的版面（渐变背景 + 名字牌 + 立绘 + 中/日字幕）。
用法: python make_video.py [--intro] [--out xxx.mp4]
"""
import argparse
import json
import os
import pathlib
import subprocess
import sys
import time

import numpy as np
import soundfile as sf

ROOT = pathlib.Path(r"E:\RentAGirl")
sys.path.insert(0, str(ROOT / "pet"))
import brain  # noqa: E402

FFMPEG = str(ROOT / "bin" / "ffmpeg.exe")
W, H = 1920, 1080
BG = ROOT / "out" / "videos" / "bg.png"
ART = ROOT / "assets_v3" / "chizuru_main.png"
OUTDIR = ROOT / "out" / "videos"
OUTDIR.mkdir(parents=True, exist_ok=True)
FONT = "C:/Windows/Fonts/msyh.ttc"
FONT_B = "C:/Windows/Fonts/msyhbd.ttc"

CREATE_NO_WINDOW = 0x08000000


def synth_line(text, dst):
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONPATH"] = r"E:\GPTSoVITS\repo;E:\GPTSoVITS\repo\GPT_SoVITS"
    p = subprocess.Popen([r"E:\GPTSoVITS\venv\Scripts\pythonw.exe", "-u", r"E:\GPTSoVITS\gsv_worker.py"],
                         stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                         cwd=r"E:\GPTSoVITS\repo", env=env, text=True, encoding="utf-8",
                         creationflags=CREATE_NO_WINDOW)
    p.stdout.readline()
    p.stdin.write(json.dumps({"text": text, "lang": "ja", "out": str(dst)}, ensure_ascii=False) + "\n")
    p.stdin.flush()
    rep = p.stdout.readline().strip()
    p.stdin.close()
    p.wait(timeout=60)
    return rep.startswith("OK") and dst.exists()


def trim_silence(w, sr):
    frame = int(0.02 * sr)
    n = max(1, w.size // frame)
    env = np.array([np.sqrt(np.mean(w[j * frame:(j + 1) * frame] ** 2)) for j in range(n)])
    thr = max(float(np.max(env)) * 0.06, 0.004)
    voiced = np.where(env > thr)[0]
    if voiced.size:
        a = max(0, (voiced[0] - 2) * frame)
        b = min(w.size, (voiced[-1] + 4) * frame)
        return w[a:b]
    return w


def intro_script():
    """自我介绍（第一支视频）。"""
    return {
        "title": "はじめまして、水原千鶴です",
        "lines": [
            {"ja": "はじめまして。水原千鶴、二十歳です", "zh": "初次见面。我是水原千鹤，20 岁。"},
            {"ja": "練馬の大学に通いながら、ちょっと変わったバイトをしてます", "zh": "在练马的大学读书，同时在打一份有点特别的工。"},
            {"ja": "レンタル彼女っていうの。一時間だけ、誰かの彼女になる仕事", "zh": "叫做「租借女友」。只当一小时别人的女朋友。"},
            {"ja": "お客さんには、いつも笑顔でいるって決めてるの", "zh": "对客人，我决定一直保持笑容。"},
            {"ja": "本当はね、女優になりたいの。舞台に立つのが夢", "zh": "其实呢，我想当演员。站在舞台上，是我的梦想。"},
            {"ja": "そのために、この仕事でお芝居の練習もしてる", "zh": "为了这个，我在这份工作里顺便练演技。"},
            {"ja": "家では、おばあちゃんと二人で暮らしてる", "zh": "在家里，我和外婆两个人住。"},
            {"ja": "疲れた日は、おばあちゃんの作るご飯が一番なのよね", "zh": "累的日子，还是外婆做的饭最好吃。"},
            {"ja": "うまく話せないことも多いけど、よかったらまた見に来てください", "zh": "我也常有说不好的时候，不嫌弃的话，下次再来看看。"},
        ],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="")
    ap.add_argument("--intro", action="store_true")
    ap.add_argument("--lines", default="")
    args = ap.parse_args()

    if args.lines:
        data = json.loads(pathlib.Path(args.lines).read_text(encoding="utf-8"))
    elif args.intro:
        data = intro_script()
    else:
        data = brain.vlog_script() or intro_script()

    print("标题:", data.get("title"), flush=True)
    segs, timings = [], []
    t = 0.0
    sr = 32000
    for i, ln in enumerate(data["lines"]):
        ja = ln.get("ja", "")
        if not ja:
            continue
        wav = OUTDIR / f"line_{i:02d}.wav"
        if not synth_line(ja, wav):
            print("合成失败:", ja[:20], flush=True)
            continue
        w, sr = sf.read(str(wav), dtype="float32")
        if w.ndim > 1:
            w = w.mean(axis=1)
        w = trim_silence(w, sr)
        dur = w.size / sr
        segs.append(w)
        segs.append(np.zeros(int(0.28 * sr), dtype=np.float32))
        # 字幕：发声开始显示，结束后 +0.5 秒消失
        timings.append((t, t + dur + 0.5, ln.get("zh", ""), ja))
        t += dur + 0.28
        print(f"  {dur:4.1f}s {ja[:26]}", flush=True)

    if not segs:
        print("没有音频")
        return
    audio = np.concatenate(segs)
    full_wav = OUTDIR / "voice.wav"
    sf.write(str(full_wav), audio, sr)
    total = audio.size / sr
    print(f"总时长 {total:.1f}s", flush=True)

    intro_off = 2.0
    srt = OUTDIR / "subs.srt"
    with srt.open("w", encoding="utf-8") as f:
        for i, (a, b, zh, ja) in enumerate(timings, 1):
            def fmt(x):
                hh = int(x // 3600); mm = int(x % 3600 // 60); ss = x % 60
                return f"{hh:02d}:{mm:02d}:{ss:06.3f}".replace(".", ",")
            f.write(f"{i}\n{fmt(a + intro_off)} --> {fmt(b + intro_off)}\n{zh}\n{ja}\n\n")

    out = pathlib.Path(args.out) if args.out else OUTDIR / f"vlog_{time.strftime('%m%d_%H%M')}.mp4"
    srt_esc = str(srt).replace(chr(92), "/").replace(":", chr(92) + ":")
    title = str(data.get("title", "")).replace(":", "：").replace("'", "’")

    from make_scenes import build as build_scenes, make_char_frame
    from PIL import Image
    scenes = build_scenes(1)          # 第一句用她的立绘 + AI 场景
    chars = (sorted(pathlib.Path(r"E:\RentAGirl\assets_i2i").glob("i2i_*.png")) or sorted(pathlib.Path(r"E:\RentAGirl\assets_web").glob("web_*.png")) or sorted(pathlib.Path(r"E:\RentAGirl\out\ai_char").glob("char_*.png")))
    if not chars:
        chars = [ROOT / "assets_v3" / "chizuru_main.png"]
    # 第一句：立绘场景；其余按台词配 AI 角色图
    frames = list(scenes)
    for i in range(1, len(timings)):
        src = chars[(i - 1) % len(chars)]
        p = OUTDIR / "scenes" / f"charframe_{i:02d}.png"
        p.parent.mkdir(parents=True, exist_ok=True)
        frames.append(make_char_frame(src, p))

    # 每句一段「缓慢推近 + 淡入淡出」，再拼起来，最后加片头/音频/字幕
    seg_dir = OUTDIR / "segs"
    seg_dir.mkdir(parents=True, exist_ok=True)
    seg_files = []
    for i, (a, b, zh, ja) in enumerate(timings):
        end = timings[i + 1][0] if i + 1 < len(timings) else total + 0.6
        dur = max(0.8, end - a)
        seg = seg_dir / f"seg_{i:02d}.mp4"
        fade = 0.18
        vf_seg = (
            f"zoompan=z='min(zoom+0.0007,1.10)':d=1:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
            f":s={W}x{H}:fps=30,"
            f"fade=t=in:st=0:d={fade},fade=t=out:st={max(0.0, dur - fade):.2f}:d={fade},format=yuv420p"
        )
        cmd_seg = [FFMPEG, "-y", "-loop", "1", "-i", str(frames[i]), "-t", f"{dur:.3f}",
                   "-vf", vf_seg, "-c:v", "h264_mf", "-b:v", "8M", "-pix_fmt", "yuv420p", str(seg)]
        r = subprocess.run(cmd_seg, capture_output=True, text=True, encoding="utf-8",
                           errors="ignore", creationflags=CREATE_NO_WINDOW)
        if r.returncode != 0:
            print("分段失败:\n", (r.stderr or "")[-600:])
            return
        seg_files.append(seg)

    # 片头：2 秒大标题
    intro = seg_dir / "intro.mp4"
    from make_bg import make_intro
    intro_png = make_intro("水原千鶴", "はじめまして", OUTDIR / "intro.png")
    vf_intro = ("zoompan=z='min(zoom+0.0012,1.06)':d=1:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
                f":s={W}x{H}:fps=30,fade=t=in:st=0:d=0.5,fade=t=out:st=1.6:d=0.4,format=yuv420p")
    r = subprocess.run([FFMPEG, "-y", "-loop", "1", "-i", str(intro_png), "-t", "2.0",
                        "-vf", vf_intro, "-c:v", "h264_mf", "-b:v", "8M",
                        "-pix_fmt", "yuv420p", str(intro)],
                       capture_output=True, text=True, encoding="utf-8",
                       errors="ignore", creationflags=CREATE_NO_WINDOW)
    if r.returncode == 0:
        seg_files = [intro] + seg_files
        intro_sec = 2.0
    else:
        intro_sec = 0.0

    lst = OUTDIR / "segments.txt"
    with lst.open("w", encoding="utf-8") as f:
        for s in seg_files:
            f.write(f"file '{s.as_posix()}'\n")

    bgm_files = sorted(pathlib.Path(r"E:\RentAGirl\bgm").glob("*.mp3"))
    bgm = bgm_files[0] if bgm_files else None
    total_len = total + intro_sec + 0.6

    vf = (
        f"[0:v]setsar=1,subtitles='{srt_esc}'"
        f":force_style='FontName=Microsoft YaHei,FontSize=12,PrimaryColour=&H00FFFFFF,OutlineColour=&H00101010,"
        f"Outline=2,Shadow=0,Alignment=1,MarginL=56,MarginV=12'[v]"
    )
    if bgm:
        vf += (
            f";[1:a]volume=1.0[vo];"
            f"[2:a]volume=0.16,afade=t=in:st=0:d=2.5,"
            f"afade=t=out:st={max(0, total_len-4):.2f}:d=4[bg];"
            f"[vo][bg]amix=inputs=2:duration=first:dropout_transition=0[aout]"
        )
    cmd = [FFMPEG, "-y",
           "-f", "concat", "-safe", "0", "-i", str(lst),
           "-itsoffset", f"{intro_sec:.2f}", "-i", str(full_wav)]
    if bgm:
        cmd += ["-stream_loop", "-1", "-i", str(bgm)]
    cmd += ["-filter_complex", vf, "-map", "[v]"]
    cmd += ["-map", "[aout]" if bgm else "1:a"]
    cmd += ["-t", f"{total_len:.2f}",
            "-c:v", "h264_mf", "-b:v", "8M", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "160k", str(out)]
    print("编码中…", flush=True)
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                       errors="ignore", creationflags=CREATE_NO_WINDOW)
    if r.returncode != 0:
        print("ffmpeg 失败:\n", (r.stderr or "")[-1200:])
        return
    print("完成:", out, flush=True)
    print("TITLE:" + title, flush=True)
    print("FILE:" + str(out), flush=True)


if __name__ == "__main__":
    main()
