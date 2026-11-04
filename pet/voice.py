"""语音后端：优先用常驻的 GPT-SoVITS 进程（和她本人的音色同一管线）。
失败时退回 edge-tts，保证永远有声音。
"""
import json
import os
import pathlib
import subprocess
import threading
import time
import wave

ROOT = pathlib.Path(__file__).resolve().parent.parent
CACHE = ROOT / "out" / "voice"
CACHE.mkdir(parents=True, exist_ok=True)

GSV_PY = r"E:\GPTSoVITS\venv\Scripts\python.exe"
GSV_PYW = r"E:\GPTSoVITS\venv\Scripts\pythonw.exe"
GSV_WORKER = r"E:\GPTSoVITS\gsv_worker.py"
GSV_CWD = r"E:\GPTSoVITS\repo"
EDGE_VOICE = "ja-JP-NanamiNeural"

_lock = threading.Lock()
_proc = None
_ready = False
_last = None


def _start_worker():
    global _proc, _ready
    if _proc is not None and _proc.poll() is None:
        return True
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONPATH"] = r"E:\GPTSoVITS\repo;E:\GPTSoVITS\repo\GPT_SoVITS"
    try:
        CREATE_NO_WINDOW = 0x08000000
        _proc = subprocess.Popen(
            [GSV_PYW, "-u", GSV_WORKER],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL, cwd=GSV_CWD, env=env,
            text=True, encoding="utf-8", bufsize=1,
            creationflags=CREATE_NO_WINDOW,
        )
        line = _proc.stdout.readline().strip()
        _ready = line == "READY"
        if not _ready:
            print("worker not ready:", line[:120])
        return _ready
    except Exception as e:
        print("worker start failed:", e)
        _proc = None
        return False


def warmup():
    threading.Thread(target=_start_worker, daemon=True).start()


def _synth_gsv(text, lang, dst, attempt=0):
    global _proc, _ready
    if not _ready and not _start_worker():
        return False
    with _lock:
        try:
            _proc.stdin.write(json.dumps({"text": text, "lang": lang, "out": str(dst)},
                                         ensure_ascii=False) + "\n")
            _proc.stdin.flush()
            t0 = time.time()
            while time.time() - t0 < 90:
                line = _proc.stdout.readline().strip()
                if not line:
                    break
                if line.startswith("OK"):
                    print("voice: gsv")
                    return dst.exists()
                if line.startswith("ERR"):
                    print("gsv err:", line[:150])
                    break
        except Exception as e:
            print("gsv io err:", e)
        _proc = None
        _ready = False
    if attempt == 0:
        return _synth_gsv(text, lang, dst, attempt=1)
    return False


def _synth_edge(text, dst):
    import av
    import edge_tts
    import numpy as np

    mp3 = dst.with_suffix(".mp3")

    async def run():
        comm = edge_tts.Communicate(text, EDGE_VOICE)
        await comm.save(str(mp3))

    import asyncio
    asyncio.run(run())
    container = av.open(str(mp3))
    stream = container.streams.audio[0]
    rs = av.AudioResampler(format="s16", layout="mono", rate=24000)
    frames = []
    for frame in container.decode(stream):
        for rf in rs.resample(frame):
            frames.append(rf.to_ndarray())
    buf = np.concatenate(frames, axis=-1).reshape(-1)
    with wave.open(str(dst), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(24000)
        w.writeframes(buf.tobytes())
    return True


def _play(p):
    import winsound
    winsound.PlaySound(str(p), winsound.SND_FILENAME | winsound.SND_ASYNC)


def speak(text, lang="ja", blocking=False):
    global _last
    text = (text or "").strip()
    if not text:
        return None
    key = f"{lang}_{abs(hash(text)) % (10 ** 10)}"
    wav = CACHE / f"{key}.wav"

    def job():
        global _last
        try:
            if not wav.exists():
                if not _synth_gsv(text, lang, wav):
                    print("voice: edge fallback")
                    _synth_edge(text, wav)
            _last = wav
            _play(wav)
        except Exception as e:
            print("voice failed:", type(e).__name__, e)

    if blocking:
        job()
        return _last
    threading.Thread(target=job, daemon=True).start()
    return wav


if __name__ == "__main__":
    import sys
    t = sys.argv[1] if len(sys.argv) > 1 else "ちょっと、何言ってるのよ"
    print("wav:", speak(t, "ja", blocking=True))

