"""用 MelBand Roformer 把人声分离出来（整集）。
用法: python separate_roformer.py S01E01 [S01E02 ...]
输出: out/roformer/<ep>/vocals.wav
"""
import json
import pathlib
import sys
import time

import numpy as np
import soundfile as sf

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

REPO = pathlib.Path(r"E:\RentAGirl")
OUT = REPO / "out"
DST = OUT / "roformer"
DST.mkdir(parents=True, exist_ok=True)
MODELS = OUT / "uvr_test" / "models"


def decode_hifi(path, cut_s, sr=44100):
    import av
    c = av.open(str(path))
    st = c.streams.audio[0]
    rs = av.AudioResampler(format="flt", layout="stereo", rate=sr)
    chunks = []
    limit = int(cut_s * sr)
    for fr in c.decode(st):
        for rf in rs.resample(fr):
            chunks.append(rf.to_ndarray())
    a = np.concatenate(chunks, axis=-1).astype(np.float32)
    if a.shape[0] > 2:
        a = a[:2]
    if limit < a.shape[-1]:
        a = a[:, :limit]
    return a.T


def main():
    eps = sys.argv[1:] or ["S01E01"]
    from audio_separator.separator import Separator

    sep = Separator(model_file_dir=str(MODELS), output_dir=str(DST / "_tmp"), output_format="WAV")
    sep.load_model("vocals_mel_band_roformer.ckpt")

    for ep in eps:
        dst = DST / ep
        dst.mkdir(parents=True, exist_ok=True)
        final = dst / "vocals.wav"
        if final.exists():
            print(f"{ep}: already done", flush=True)
            continue
        src = dst / "input.wav"
        if not src.exists():
            cut = json.loads((OUT / f"{ep}.cut.json").read_text(encoding="utf-8"))["cut_s"]
            a = decode_hifi(REPO / "raw" / f"{ep}.mp4", cut)
            sf.write(str(src), a, 44100)
            print(f"{ep}: decoded {a.shape[0]/44100/60:.1f} min", flush=True)
        t0 = time.time()
        outs = sep.separate(str(src))
        voc = [o for o in outs if "(vocals)" in o][0]
        p = DST / "_tmp" / voc if (DST / "_tmp" / voc).exists() else pathlib.Path(voc)
        import shutil
        shutil.move(str(p), str(final))
        print(f"{ep}: separated in {time.time()-t0:.0f}s", flush=True)
        try:
            src.unlink()
        except OSError:
            pass


if __name__ == "__main__":
    main()
