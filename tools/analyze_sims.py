"""统计训练集片段的声纹相似度分布，按来源（gold/auto）分组，并输出不同阈值下的保留量。"""
import json
import pathlib

import numpy as np
import soundfile as sf
import torch

REPO = pathlib.Path(r"E:\RentAGirl")
DS = pathlib.Path(r"E:\GPTSoVITS\dataset2")
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
        sim = float(embed(x) @ C)
        src = "gold" if "_gold_" in p.name else "auto"
        recs.append((sim, src, float(w.size / sr)))
        if (i + 1) % 300 == 0:
            print("done", i + 1, flush=True)

    for src in ("gold", "auto", "all"):
        vals = np.array([r[0] for r in recs if src == "all" or r[1] == src])
        if vals.size == 0:
            continue
        qs = np.percentile(vals, [10, 25, 50, 75, 90])
        print(f"{src:5s} n={vals.size:5d} p10={qs[0]:.2f} p25={qs[1]:.2f} median={qs[2]:.2f} "
              f"p75={qs[3]:.2f} p90={qs[4]:.2f}", flush=True)

    for th in (0.45, 0.50, 0.55, 0.60, 0.65):
        keep = [r for r in recs if r[0] >= th]
        mins = sum(r[2] for r in keep) / 60
        print(f"th>={th:.2f}: {len(keep):5d} clips / {mins:5.1f} min", flush=True)

    out = DS.parent / "sims.json"
    out.write_text(json.dumps([{"sim": r[0], "src": r[1], "dur": r[2]} for r in recs]), encoding="utf-8")
    print("saved", out, flush=True)


if __name__ == "__main__":
    main()
