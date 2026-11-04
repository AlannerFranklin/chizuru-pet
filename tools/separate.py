"""用 demucs 把剧集音轨分离成人声/伴奏。
用法: python separate.py S01E01 [S01E02 ...]
输出: out/separated/<ep>/vocals.wav
"""
import json
import pathlib
import subprocess
import sys

import av
import numpy as np
import soundfile as sf

REPO = pathlib.Path(r"E:\RentAGirl")
OUT = REPO / "out" / "separated"
OUT.mkdir(parents=True, exist_ok=True)
SR = 44100


def decode_hifi(path, cut_s, sr=SR):
    """解码成 44.1k 立体声，截到正片结束。"""
    container = av.open(str(path))
    stream = container.streams.audio[0]
    resampler = av.AudioResampler(format="flt", layout="stereo", rate=sr)
    chunks = []
    limit = int(cut_s * sr)
    for frame in container.decode(stream):
        for rf in resampler.resample(frame):
            chunks.append(rf.to_ndarray())
    audio = np.concatenate(chunks, axis=-1).astype(np.float32)
    if audio.shape[0] > 2:
        audio = audio[:2]
    if limit < audio.shape[-1]:
        audio = audio[:, :limit]
    return audio.T  # (n, 2)


def main():
    eps = sys.argv[1:] or ["S01E01"]
    for ep in eps:
        dst_dir = OUT / ep
        dst_dir.mkdir(parents=True, exist_ok=True)
        wav_in = dst_dir / "input.wav"
        if (dst_dir / "vocals.wav").exists():
            print(f"{ep}: already done", flush=True)
            continue
        if not wav_in.exists():
            cut = json.loads((REPO / "out" / f"{ep}.cut.json").read_text(encoding="utf-8"))["cut_s"]
            audio = decode_hifi(REPO / "raw" / f"{ep}.mp4", cut)
            sf.write(str(wav_in), audio, SR)
            print(f"{ep}: audio {audio.shape[0]/SR/60:.1f} min", flush=True)
        cmd = [sys.executable, "-m", "demucs", "--two-stems=vocals",
               "-n", "htdemucs", "-o", str(dst_dir), str(wav_in)]
        print("running demucs...", flush=True)
        subprocess.run(cmd, check=True)
        produced = dst_dir / "htdemucs" / "input" / "vocals.wav"
        if produced.exists():
            produced.replace(dst_dir / "vocals.wav")
            print(f"{ep}: vocals ok", flush=True)
            try:
                wav_in.unlink()
            except OSError:
                pass


if __name__ == "__main__":
    main()
