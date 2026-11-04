"""清理错标：对每个片段做三重校验
1) 与本集/全体均值相似度（已有）
2) 1-NN：与「人工金标片段」的最近邻相似度（比均值更严格）
3) F0（基频中位数）：她的音域范围
用金标片段当正样本校准阈值。
"""
import json
import pathlib

import numpy as np
import soundfile as sf
import torch

DS = pathlib.Path(r"E:\GPTSoVITS\dataset2")
REPO = pathlib.Path(r"E:\RentAGirl")
C = np.load(REPO / "out" / "chizuru_enroll.npy")
EMB = None


def embed(wav):
    global EMB
    if EMB is None:
        from pyannote.audio import Model
        EMB = Model.from_pretrained(r"E:\test\pyannote\emb")
    if wav.size < 8000:
        wav = np.pad(wav, (0, 8000 - wav.size))
    t = torch.from_numpy(wav.astype(np.float32)).unsqueeze(0).unsqueeze(0)
    with torch.no_grad():
        e = EMB(t).squeeze().cpu().numpy()
    return e / (np.linalg.norm(e) + 1e-9)


def f0_median(wav, sr=16000):
    if wav.size < sr // 5:
        return 0.0
    frame = int(0.04 * sr)
    hop = int(0.02 * sr)
    vals = []
    lo, hi = int(sr / 400), int(sr / 80)
    for i in range(0, wav.size - frame, hop):
        seg = wav[i:i + frame] * np.hanning(frame)
        ac = np.correlate(seg, seg, "full")[frame - 1:]
        if ac[0] <= 1e-6:
            continue
        ac = ac / ac[0]
        seg_lo = max(lo, 1)
        seg_hi = min(hi, ac.size - 1)
        if seg_hi <= seg_lo:
            continue
        k = seg_lo + int(np.argmax(ac[seg_lo:seg_hi]))
        if ac[k] > 0.3:
            vals.append(sr / k)
    return float(np.median(vals)) if vals else 0.0


def main():
    lines = [l for l in (DS / "list.txt").read_text(encoding="utf-8").strip().split("\n") if l]
    recs = []
    for i, line in enumerate(lines):
        parts = line.split("|")
        p = pathlib.Path(parts[0])
        w, sr = sf.read(str(p), dtype="float32")
        if w.ndim > 1:
            w = w.mean(axis=1)
        n = int(round(w.size * 16000 / sr))
        x = np.interp(np.linspace(0, w.size - 1, n), np.arange(w.size), w).astype(np.float32)
        e = embed(x)
        recs.append({
            "path": str(p), "src": "gold" if "_gold_" in p.name else "auto",
            "sim": float(e @ C), "emb": e, "dur": float(w.size / sr),
            "f0": f0_median(x),
        })
        if (i + 1) % 300 == 0:
            print("done", i + 1, flush=True)

    gold = [r for r in recs if r["src"] == "gold"]
    G = np.stack([r["emb"] for r in gold])
    for r in recs:
        r["nn"] = float(np.max(G @ r["emb"]))

    def q(vals, name):
        a = np.array(vals)
        print(f"{name:12s} p5={np.percentile(a,5):.2f} p25={np.percentile(a,25):.2f} "
              f"med={np.median(a):.2f} p75={np.percentile(a,75):.2f} p95={np.percentile(a,95):.2f}", flush=True)

    q([r["sim"] for r in gold], "gold sim")
    q([r["nn"] for r in gold], "gold 1NN")
    q([r["f0"] for r in gold if r["f0"] > 0], "gold f0")
    auto = [r for r in recs if r["src"] == "auto"]
    q([r["sim"] for r in auto], "auto sim")
    q([r["nn"] for r in auto], "auto 1NN")
    q([r["f0"] for r in auto if r["f0"] > 0], "auto f0")

    meta = [{"path": r["path"], "src": r["src"], "sim": r["sim"], "nn": r["nn"],
             "f0": r["f0"], "dur": r["dur"]} for r in recs]
    (DS.parent / "clean_meta.json").write_text(json.dumps(meta), encoding="utf-8")
    print("saved clean_meta.json", flush=True)


if __name__ == "__main__":
    main()
