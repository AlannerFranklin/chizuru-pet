"""对 dataset6 计算声纹相似度，按阈值筛选，输出可训练列表和审核索引。"""
import json
import pathlib
import sys

import numpy as np
import soundfile as sf
import torch

DS = pathlib.Path(r"E:\GPTSoVITS\dataset6")
TH = float(sys.argv[1]) if len(sys.argv) > 1 else 0.50
C = np.load(r"E:\RentAGirl\out\chizuru_enroll.npy")
EMB = None


def embed(path):
    global EMB
    if EMB is None:
        from pyannote.audio import Model
        EMB = Model.from_pretrained(r"E:\test\pyannote\emb")
    x, sr = sf.read(str(path), dtype="float32")
    if x.ndim > 1:
        x = x.mean(axis=1)
    n = int(x.size * 16000 / sr)
    y = np.interp(np.linspace(0, x.size - 1, n), np.arange(x.size), x).astype(np.float32)
    t = torch.from_numpy(y).unsqueeze(0).unsqueeze(0)
    with torch.no_grad():
        e = EMB(t).squeeze().cpu().numpy()
    e = e / (np.linalg.norm(e) + 1e-9)
    return float(e @ C), round(x.size / sr, 2)


def main():
    lines = [l for l in (DS / "list.txt").read_text(encoding="utf-8").strip().split("\n") if l]
    keep, meta = [], []
    for i, l in enumerate(lines):
        p = pathlib.Path(l.split("|")[0])
        text = "|".join(l.split("|")[3:])
        sim, dur = embed(p)
        src = "gold" if "_gold_" in p.name else "auto"
        meta.append({"id": p.name, "file": str(p), "ja": text, "sim": round(sim, 3),
                     "dur": dur, "src": src})
        if sim >= TH:
            keep.append(l)
        if (i + 1) % 400 == 0:
            print("done", i + 1, flush=True)
    with (DS / "list_filtered.txt").open("w", encoding="utf-8") as f:
        f.write("\n".join(keep) + "\n")
    (DS / "index.json").write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8")
    total = sum(m["dur"] for m in meta if m["sim"] >= TH)
    print(f"keep {len(keep)} / {len(lines)}  ({total/60:.1f} min) at sim>={TH}", flush=True)


if __name__ == "__main__":
    main()
