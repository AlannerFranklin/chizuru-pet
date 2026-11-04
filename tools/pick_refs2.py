"""按模式从原片切出「情绪参考音频」（每种模式一段 3~7 秒）。
输出: E:\GPTSoVITS\refs\<mode>.wav 和 refs.json
"""
import json, pathlib
import numpy as np, soundfile as sf, av

REPO = pathlib.Path(r"E:\RentAGirl")
OUT = REPO / "out"
DST = pathlib.Path(r"E:\GPTSoVITS\refs")
DST.mkdir(parents=True, exist_ok=True)
SR = 32000


def decode_raw(path, cut_s, sr=44100):
    c = av.open(str(path))
    st = c.streams.audio[0]
    rs = av.AudioResampler(format="flt", layout="mono", rate=sr)
    chunks = []
    limit = int(cut_s * sr)
    for fr in c.decode(st):
        for rf in rs.resample(fr):
            chunks.append(rf.to_ndarray().reshape(-1))
    a = np.concatenate(chunks).astype(np.float32)
    return a[:limit] if limit < a.size else a


def main():
    rows = [json.loads(l) for l in (OUT / "chizuru_gold.jsonl").open(encoding="utf-8")]
    by_mode = {}
    for r in rows:
        by_mode.setdefault(r.get("mode") or "素", []).append(r)

    cache = {}
    chosen = {}
    for mode, items in by_mode.items():
        cands = []
        for r in items:
            ep = r["ep"]
            end = r.get("end")
            if end is None:
                continue
            dur = end - r["start"]
            if not (3.0 <= dur <= 7.5):
                continue
            if ep not in cache:
                cut = json.loads((OUT / f"{ep}.cut.json").read_text(encoding="utf-8"))["cut_s"]
                cache[ep] = decode_raw(REPO / "raw" / f"{ep}.mp4", cut)
            a = cache[ep][int(r["start"] * 44100):int(end * 44100)]
            if a.size == 0:
                continue
            rms = float(np.sqrt(np.mean(a ** 2)))
            peak = float(np.max(np.abs(a)))
            if rms < 0.05 or peak > 0.98:
                continue
            cands.append((dur, rms, r, a))
        if not cands:
            print(f"{mode}: no candidate")
            continue
        cands.sort(key=lambda x: -x[1])
        dur, rms, r, a = cands[0]
        arr = np.interp(np.linspace(0, a.size - 1, int(a.size * SR / 44100)), np.arange(a.size), a).astype(np.float32)
        arr = arr / (np.max(np.abs(arr)) + 1e-6) * 0.95
        p = DST / f"{mode}.wav"
        sf.write(str(p), arr, SR)
        chosen[mode] = {"file": str(p), "text": r["ja"], "dur": round(dur, 1), "rms": round(rms, 3), "ep": r["ep"]}
        print(f"{mode}: {dur:.1f}s rms={rms:.3f} {r['ep']} | {r['ja'][:36]}")

    (DST / "refs.json").write_text(json.dumps(chosen, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
