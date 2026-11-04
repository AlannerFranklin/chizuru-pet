"""从分离出的人声里，按金标时间戳切出千鹤的干净语音，构建 GPT-SoVITS 训练集。
用法: python build_voice_dataset.py S01E01 S01E02 ...
输出: E:\GPTSoVITS\dataset\raw\<ep>\*.wav + list.txt
"""
import json
import pathlib
import sys

import numpy as np
import soundfile as sf

REPO = pathlib.Path(r"E:\RentAGirl")
OUT = REPO / "out"
SEP = OUT / "separated"
DST_ROOT = pathlib.Path(r"E:\GPTSoVITS\dataset")
DST = DST_ROOT / "raw"
DST.mkdir(parents=True, exist_ok=True)
SR = 32000

MIN_DUR, MAX_DUR = 1.2, 9.0
MIN_RMS = 0.012


def resample(audio, src_sr, dst_sr):
    if src_sr == dst_sr:
        return audio
    n = int(round(audio.size * dst_sr / src_sr))
    idx = np.linspace(0, audio.size - 1, n)
    return np.interp(idx, np.arange(audio.size), audio).astype(np.float32)


def decode_raw(path, cut_s, sr=44100):
    """原片音轨（44.1k 立体声→单声道），用于不走分轨时切素材。"""
    import av
    container = av.open(str(path))
    stream = container.streams.audio[0]
    rs = av.AudioResampler(format="flt", layout="mono", rate=sr)
    chunks = []
    limit = int(cut_s * sr)
    for frame in container.decode(stream):
        for rf in rs.resample(frame):
            chunks.append(rf.to_ndarray().reshape(-1))
    audio = np.concatenate(chunks).astype(np.float32)
    return audio[:limit] if limit < audio.size else audio


def main():
    eps = [a for a in sys.argv[1:] if not a.startswith("--")]
    use_raw = "--raw" in sys.argv
    eps = eps or ["S01E01"]
    rows = [json.loads(l) for l in (OUT / "chizuru_gold.jsonl").open(encoding="utf-8")]
    kept = []
    for ep in eps:
        if use_raw:
            cut = json.loads((OUT / f"{ep}.cut.json").read_text(encoding="utf-8"))["cut_s"]
            audio_raw = decode_raw(REPO / "raw" / f"{ep}.mp4", cut)
            audio, sr = audio_raw, 44100
        else:
            vpath = SEP / ep / "vocals.wav"
            if not vpath.exists():
                print(f"{ep}: no vocals, skip")
                continue
            audio, sr = sf.read(str(vpath), dtype="float32")
            if audio.ndim > 1:
                audio = audio.mean(axis=1)
        ep_dir = DST / ep
        ep_dir.mkdir(parents=True, exist_ok=True)
        items = [r for r in rows if r["ep"] == ep and r.get("conf") == "high"]
        asr = {round(x["start"], 1): x for x in
               json.loads((OUT / f"{ep}.asr.json").read_text(encoding="utf-8"))}

        # 时间轴不做偏移修正：语料时间戳是准的，错的多半是分轨或静音，交给声纹过滤筛掉
        best_off = 0.0

        n = 0
        for r in items:
            end = r.get("end")
            if end is None:
                a2 = asr.get(round(r["start"], 1))
                end = a2["end"] if a2 else None
            if end is None:
                continue
            a = max(0.0, r["start"] + best_off - 0.08)
            b = min(audio.size / sr, (end + best_off) + 0.12)
            dur = b - a
            if not (MIN_DUR <= dur <= MAX_DUR):
                continue
            seg = audio[int(a * sr):int(b * sr)]
            if seg.size == 0:
                continue
            rms = float(np.sqrt(np.mean(seg ** 2)))
            peak = float(np.max(np.abs(seg)))
            if rms < MIN_RMS or peak > 0.99:
                continue
            seg = resample(seg, sr, SR)
            seg = seg / (np.max(np.abs(seg)) + 1e-6) * 0.9
            name = f"{ep}_{n:03d}.wav"
            sf.write(str(ep_dir / name), seg, SR)
            text = r["ja"].strip()
            if text:
                kept.append((str(ep_dir / name), text))
                n += 1
        print(f"{ep}: kept {n} / {len(items)}")

    list_path = DST_ROOT / "list.txt"
    with list_path.open("w", encoding="utf-8") as f:
        for p, t in kept:
            f.write(f"{p}|chizuru|JP|{t}\n")
    print("total clips:", len(kept), "->", list_path)


if __name__ == "__main__":
    main()
