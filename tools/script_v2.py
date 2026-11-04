"""按新文案合成语音：生成 voice2.wav + subs2.srt。"""
import json
import os
import pathlib
import subprocess

import numpy as np
import soundfile as sf

OUT = pathlib.Path(r"E:\RentAGirl\out\videos")
CREATE_NO_WINDOW = 0x08000000

LINES = [
    ("ねえ、聞いて。私、ちょっと変わったバイトしてるの", "喂，听我说——我在打一份有点奇怪的工"),
    ("レンタル彼女。一時間だけ、誰かの隣にいる仕事", "租借女友。只当一小时，待在谁身边"),
    ("本当の名前は、一ノ瀬千鶴。……内緒ね", "真名是一之濑千鹤。……要保密哦"),
    ("笑顔は仕事。でも、作り笑いじゃないよ", "笑容是工作，但不是假笑"),
    ("女優になりたくて、毎晩台本を読んでる", "想当演员，每晚都在读剧本"),
    ("おばあちゃんは、私の演技を一度も見たことがない", "外婆一次都没看过我演戏"),
    ("だからいつか、舞台の一番前で見てほしいの", "所以哪天站上舞台，想让她坐在最前排"),
    ("夢って、笑われるようなものほど、本気だったりする", "梦想这种东西，越像笑话的，往往越认真"),
    ("で、あなたは何になりたいの？", "那么，你想成为什么呢？"),
    ("また話しに来てね。待ってるから", "下次再来聊吧，我等着你"),
]


def synth(text, dst):
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
    p.wait(timeout=90)
    return rep.startswith("OK")


def trim(w, sr):
    frame = int(0.02 * sr)
    n = max(1, w.size // frame)
    env = np.array([np.sqrt(np.mean(w[j * frame:(j + 1) * frame] ** 2)) for j in range(n)])
    thr = max(float(np.max(env)) * 0.06, 0.004)
    v = np.where(env > thr)[0]
    if v.size:
        return w[max(0, (v[0] - 2) * frame):min(w.size, (v[-1] + 4) * frame)]
    return w


def main():
    segs, timings = [], []
    t = 0.0
    sr = 32000
    for i, (ja, zh) in enumerate(LINES):
        wav = OUT / f"l2_{i:02d}.wav"
        if not synth(ja, wav):
            print("合成失败", ja[:16])
            continue
        w, sr = sf.read(str(wav), dtype="float32")
        if w.ndim > 1:
            w = w.mean(axis=1)
        w = trim(w, sr)
        d = w.size / sr
        segs.append(w)
        segs.append(np.zeros(int(0.26 * sr), dtype=np.float32))
        timings.append((t, t + d + 0.5, zh, ja))
        t += d + 0.26
        print(f"  {d:4.1f}s {ja[:26]}")

    audio = np.concatenate(segs)
    sf.write(str(OUT / "voice2.wav"), audio, sr)
    total = audio.size / sr
    print("总时长", round(total, 1))

    intro = 2.0
    with (OUT / "subs2.srt").open("w", encoding="utf-8") as f:
        for i, (a, b, zh, ja) in enumerate(timings, 1):
            def fmt(x):
                hh = int(x // 3600); mm = int(x % 3600 // 60); ss = x % 60
                return f"{hh:02d}:{mm:02d}:{ss:06.3f}".replace(".", ",")
            f.write(f"{i}\n{fmt(a+intro)} --> {fmt(b+intro)}\n{zh}\n{ja}\n\n")
    print("done")


if __name__ == "__main__":
    main()
