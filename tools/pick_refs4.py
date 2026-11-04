"""从 Roformer 分离出的人声里，按模式各挑一段参考音频（不做任何降噪）。
输出: E:\GPTSoVITS\refs\v4\<mode>.wav + refs.json
"""
import json, pathlib
import numpy as np, soundfile as sf

REPO = pathlib.Path(r"E:\RentAGirl")
OUT = REPO / "out"
SEP = OUT / "roformer"
DST = pathlib.Path(r"E:\GPTSoVITS\refs\v4")
DST.mkdir(parents=True, exist_ok=True)
SR = 32000
EPS = [p.name for p in SEP.glob("S*") if (p / "vocals.wav").exists()]


def metrics(w, sr):
    frame = int(0.02 * sr)
    n = max(1, w.size // frame)
    rms = np.array([np.sqrt(np.mean(w[i * frame:(i + 1) * frame] ** 2)) for i in range(n)])
    thr = np.percentile(rms, 90) * 0.15
    return float(np.mean(rms > thr)), float(np.percentile(rms, 10))


def main():
    rows = [json.loads(l) for l in (OUT / "chizuru_gold.jsonl").open(encoding="utf-8")]
    cache = {}
    chosen = {}
    for mode in ("素", "営業", "衝突", "软肋"):
        items = [r for r in rows if (r.get("mode") or "素") == mode and r["ep"] in EPS]
        best = None
        for r in items:
            end = r.get("end")
            if end is None:
                continue
            dur = end - r["start"]
            if not (3.4 <= dur <= 7.0):
                continue
            ep = r["ep"]
            if ep not in cache:
                w, sr = sf.read(str(SEP / ep / "vocals.wav"), dtype="float32")
                cache[ep] = (w.mean(axis=1) if w.ndim > 1 else w, sr)
            w, sr = cache[ep]
            seg = w[int(r["start"] * sr):int(end * sr)]
            if seg.size < int(0.8 * sr):
                continue
            act, floor = metrics(seg, sr)
            if act < 0.85 or floor > 0.012:
                continue
            score = act - floor * 20
            if best is None or score > best[0]:
                best = (score, r, seg, sr, act, floor)
        if best is None:
            print(f"{mode}: 没有合格候选", flush=True)
            continue
        _, r, seg, sr, act, floor = best
        n = int(seg.size * SR / sr)
        arr = np.interp(np.linspace(0, seg.size - 1, n), np.arange(seg.size), seg).astype(np.float32)
        arr = arr / (np.max(np.abs(arr)) + 1e-6) * 0.9
        p = DST / f"{mode}.wav"
        sf.write(str(p), arr, SR)
        chosen[mode] = {"file": str(p), "text": r["ja"], "ep": r["ep"], "dur": round(arr.size / SR, 2)}
        print(f"{mode}: {arr.size/SR:.2f}s act={act:.2f} floor={floor:.4f} {r['ep']} | {r['ja'][:30]}", flush=True)

    (DST / "refs.json").write_text(json.dumps(chosen, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
