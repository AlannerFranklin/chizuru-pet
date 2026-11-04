"""扩大语音训练集：用全部人工金标 + 自动标注行，从原片切片。
用法: python build_voice_dataset2.py
输出: E:\GPTSoVITS\dataset2\raw\*.wav + list.txt
"""
import json
import pathlib

import numpy as np
import soundfile as sf

REPO = pathlib.Path(r"E:\RentAGirl")
OUT = REPO / "out"
DST = pathlib.Path(r"E:\GPTSoVITS\dataset2\raw")
DST.mkdir(parents=True, exist_ok=True)
SR = 32000
MIN_DUR, MAX_DUR = 1.0, 9.0
MIN_RMS = 0.010


def decode_raw(path, cut_s, sr=44100):
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
    gold = [json.loads(l) for l in (OUT / "chizuru_gold.jsonl").open(encoding="utf-8")]
    auto = [json.loads(l) for l in (OUT / "chizuru_auto.jsonl").open(encoding="utf-8")]
    rows = [(r, "gold") for r in gold] + [(r, "auto") for r in auto if r.get("score", 0) >= 0.55]
    by_ep = {}
    for r, src in rows:
        by_ep.setdefault(r["ep"], []).append((r, src))
    print("episodes:", len(by_ep), "rows:", len(rows), flush=True)

    kept = 0
    for ep, items in sorted(by_ep.items()):
        mp4 = REPO / "raw" / f"{ep}.mp4"
        cut_p = OUT / f"{ep}.cut.json"
        asr_p = OUT / f"{ep}.asr.json"
        if not (mp4.exists() and cut_p.exists() and asr_p.exists()):
            print(f"{ep}: missing source", flush=True)
            continue
        cut = json.loads(cut_p.read_text(encoding="utf-8"))["cut_s"]
        asr = {round(x["start"], 1): x for x in json.loads(asr_p.read_text(encoding="utf-8"))}
        audio = decode_raw(mp4, cut)
        n = 0
        for r, src in items:
            end = r.get("end")
            if end is None:
                a2 = asr.get(round(r["start"], 1))
                end = a2["end"] if a2 else None
            if end is None:
                continue
            a = max(0.0, r["start"] - 0.08)
            b = min(audio.size / 44100, end + 0.12)
            if not (MIN_DUR <= b - a <= MAX_DUR):
                continue
            seg = audio[int(a * 44100):int(b * 44100)]
            if seg.size < 1000:
                continue
            if float(np.sqrt(np.mean(seg ** 2))) < MIN_RMS:
                continue
            arr = np.interp(np.linspace(0, seg.size - 1, int(seg.size * SR / 44100)),
                            np.arange(seg.size), seg).astype(np.float32)
            arr = arr / (np.max(np.abs(arr)) + 1e-6) * 0.9
            name = f"{ep}_{src}_{n:03d}.wav"
            sf.write(str(DST / name), arr, SR)
            with (DST / ".." / "list.txt").open("a", encoding="utf-8") as f:
                f.write(f"{DST / name}|chizuru|JP|{r['ja'].strip()}\n")
            n += 1
            kept += 1
        print(f"{ep}: {n} clips", flush=True)
    print("total", kept, flush=True)


if __name__ == "__main__":
    main()
