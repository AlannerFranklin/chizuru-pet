"""逐段分离：只对"底噪偏高"的片段做 Roformer 人声分离，干净的片段直接用原声。
输出 E:\\GPTSoVITS\\dataset6
"""
import json
import pathlib
import shutil

import numpy as np
import soundfile as sf

SR = 32000
DS2 = pathlib.Path(r"E:\GPTSoVITS\dataset2")
DST = pathlib.Path(r"E:\GPTSoVITS\dataset6")
RAW = DST / "raw"
RAW.mkdir(parents=True, exist_ok=True)
TMP = DST / "_tmp"
TMP.mkdir(parents=True, exist_ok=True)

FLOOR_TH = 0.010


def floor_of(w, sr):
    frame = int(0.02 * sr)
    n = max(1, w.size // frame)
    rms = np.array([np.sqrt(np.mean(w[i * frame:(i + 1) * frame] ** 2)) for i in range(n)])
    return float(np.percentile(rms, 10))


def main():
    lines = [l for l in (DS2 / "list.txt").read_text(encoding="utf-8").strip().split("\n") if l]
    print("clips", len(lines), flush=True)

    from audio_separator.separator import Separator
    sep = Separator(model_file_dir=r"E:\RentAGirl\out\uvr_test\models",
                    output_dir=str(TMP), output_format="WAV")
    sep.load_model("vocals_mel_band_roformer.ckpt")

    kept = []
    n_sep = 0
    for i, line in enumerate(lines):
        parts = line.split("|")
        src = pathlib.Path(parts[0])
        text = "|".join(parts[3:])
        out = RAW / src.name
        if not src.exists():
            continue
        w, sr = sf.read(str(src), dtype="float32")
        if w.ndim > 1:
            w = w.mean(axis=1)
        f = floor_of(w, sr)
        if f > FLOOR_TH:
            tmp_in = TMP / "in.wav"
            sf.write(str(tmp_in), w, sr)
            try:
                outs = sep.separate(str(tmp_in))
                voc = [o for o in outs if "(vocals)" in o][0]
                vp = TMP / voc if (TMP / voc).exists() else pathlib.Path(voc)
                v, vsr = sf.read(str(vp), dtype="float32")
                if v.ndim > 1:
                    v = v.mean(axis=1)
                if v.size < int(0.5 * vsr):
                    v, vsr = w, sr
                else:
                    n = int(v.size * SR / vsr)
                    v = np.interp(np.linspace(0, v.size - 1, n), np.arange(v.size), v).astype(np.float32)
                    vsr = SR
                    try:
                        vp.unlink()
                    except OSError:
                        pass
                n_sep += 1
            except Exception as e:
                print("sep failed", src.name, type(e).__name__, flush=True)
                v, vsr = w, sr
        else:
            v, vsr = w, sr
        if vsr != SR:
            n = int(v.size * SR / vsr)
            v = np.interp(np.linspace(0, v.size - 1, n), np.arange(v.size), v).astype(np.float32)
        v = v / (np.max(np.abs(v)) + 1e-6) * 0.9
        sf.write(str(out), v, SR)
        kept.append((out, text))
        if (i + 1) % 100 == 0:
            print(f"{i+1}/{len(lines)} separated={n_sep}", flush=True)

    with (DST / "list.txt").open("w", encoding="utf-8") as f:
        for p, text in kept:
            f.write(f"{p}|chizuru|JP|{text}\n")
    print("done clips", len(kept), "separated", n_sep, flush=True)


if __name__ == "__main__":
    main()
