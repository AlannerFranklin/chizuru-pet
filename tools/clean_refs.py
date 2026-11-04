"""把 demucs 分离出的人声整理成「干净参考音频」：高通 + 归一化 + 去静音。"""
import json, pathlib
import numpy as np, soundfile as sf
from scipy.signal import butter, sosfilt

REFS = json.loads(pathlib.Path(r"E:\GPTSoVITS\refs\refs.json").read_text(encoding="utf-8"))
SEP = pathlib.Path(r"E:\GPTSoVITS\refs\sep\htdemucs")
DST = pathlib.Path(r"E:\GPTSoVITS\refs\clean")
DST.mkdir(parents=True, exist_ok=True)
SR = 32000

sos = butter(4, 90, btype="highpass", fs=44100, output="sos")

out = {}
for mode, info in REFS.items():
    src = SEP / mode / "vocals.wav"
    if not src.exists():
        print(mode, "missing")
        continue
    w, sr = sf.read(str(src), dtype="float32")
    if w.ndim > 1:
        w = w.mean(axis=1)
    w = sosfilt(sos, w).astype(np.float32)
    # 去首尾静音
    thr = 0.02 * float(np.max(np.abs(w)))
    idx = np.where(np.abs(w) > thr)[0]
    if idx.size:
        w = w[max(0, idx[0] - int(0.05 * sr)): idx[-1] + int(0.05 * sr)]
    w = w / (np.max(np.abs(w)) + 1e-6) * 0.9
    n = int(w.size * SR / sr)
    arr = np.interp(np.linspace(0, w.size - 1, n), np.arange(w.size), w).astype(np.float32)
    p = DST / f"{mode}.wav"
    sf.write(str(p), arr, SR)
    out[mode] = {**info, "file": str(p), "clean_dur": round(arr.size / SR, 2)}
    print(mode, "->", round(arr.size / SR, 2), "s")

(DST / "refs_clean.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
