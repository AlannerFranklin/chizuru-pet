"""用 Roformer 分离出的人声，重建语音训练集。
用法: python build_voice_dataset3.py            # 切全部
      python build_voice_dataset3.py 0.55       # 同时按声纹相似度筛选
输出: E:\GPTSoVITS\dataset5\{raw,list.txt}
"""
import json
import pathlib
import sys

import numpy as np
import soundfile as sf

REPO = pathlib.Path(r"E:\RentAGirl")
OUT = REPO / "out"
SEP = OUT / "roformer"
DST = pathlib.Path(r"E:\GPTSoVITS\dataset5")
RAW = DST / "raw"
RAW.mkdir(parents=True, exist_ok=True)
SR = 32000
MIN_DUR, MAX_DUR = 1.0, 9.0
MIN_RMS = 0.010


def main():
    vals = [a for a in sys.argv[1:] if not a.startswith("--")]
    th = float(vals[0]) if vals else 0.0

    gold = [json.loads(l) for l in (OUT / "chizuru_gold.jsonl").open(encoding="utf-8")]
    auto = [json.loads(l) for l in (OUT / "chizuru_auto.jsonl").open(encoding="utf-8")]
    rows = [(r, "gold") for r in gold] + [(r, "auto") for r in auto if r.get("score", 0) >= 0.55]
    by_ep = {}
    for r, src in rows:
        by_ep.setdefault(r["ep"], []).append((r, src))

    kept = []
    for ep, items in sorted(by_ep.items()):
        vp = SEP / ep / "vocals.wav"
        if not vp.exists():
            print(f"{ep}: 没有分离结果，跳过", flush=True)
            continue
        w, sr = sf.read(str(vp), dtype="float32")
        if w.ndim > 1:
            w = w.mean(axis=1)
        asr = {round(x["start"], 1): x for x in
               json.loads((OUT / f"{ep}.asr.json").read_text(encoding="utf-8"))}
        n = 0
        for r, src in items:
            end = r.get("end")
            if end is None:
                a2 = asr.get(round(r["start"], 1))
                end = a2["end"] if a2 else None
            if end is None:
                continue
            a = max(0.0, r["start"] - 0.08)
            b = min(w.size / sr, end + 0.12)
            if not (MIN_DUR <= b - a <= MAX_DUR):
                continue
            seg = w[int(a * sr):int(b * sr)]
            if seg.size < 1000 or float(np.sqrt(np.mean(seg ** 2))) < MIN_RMS:
                continue
            k = int(seg.size * SR / sr)
            arr = np.interp(np.linspace(0, seg.size - 1, k), np.arange(seg.size), seg).astype(np.float32)
            arr = arr / (np.max(np.abs(arr)) + 1e-6) * 0.9
            name = f"{ep}_{src}_{n:03d}.wav"
            sf.write(str(RAW / name), arr, SR)
            kept.append((RAW / name, r["ja"].strip(), r.get("mode") or "素", src, ep))
            n += 1
        print(f"{ep}: {n} 段", flush=True)

    with (DST / "list.txt").open("w", encoding="utf-8") as f:
        for p, text, mode, src, ep in kept:
            f.write(f"{p}|chizuru|JP|{text}\n")
    print("total", len(kept), flush=True)

    if th > 0:
        import torch
        from pyannote.audio import Model
        C = np.load(REPO / "out" / "chizuru_enroll.npy")
        emb = Model.from_pretrained(r"E:\test\pyannote\emb")
        keep = []
        for p, text, mode, src, ep in kept:
            x, sr = sf.read(str(p), dtype="float32")
            n = int(x.size * 16000 / sr)
            y = np.interp(np.linspace(0, x.size - 1, n), np.arange(x.size), x).astype(np.float32)
            t = torch.from_numpy(y).unsqueeze(0).unsqueeze(0)
            with torch.no_grad():
                e = emb(t).squeeze().cpu().numpy()
            e = e / (np.linalg.norm(e) + 1e-9)
            if float(e @ C) >= th:
                keep.append((p, text, mode, src, ep))
        with (DST / "list_filtered.txt").open("w", encoding="utf-8") as f:
            for p, text, mode, src, ep in keep:
                f.write(f"{p}|chizuru|JP|{text}\n")
        meta = [{"id": p.name, "file": str(p), "ja": text, "mode": mode, "src": src, "ep": ep}
                for p, text, mode, src, ep in keep]
        (DST / "index.json").write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8")
        print(f"filtered {len(keep)} / {len(kept)} at sim>={th}", flush=True)


if __name__ == "__main__":
    main()
