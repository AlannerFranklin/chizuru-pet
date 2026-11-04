"""用全部人工金标重算千鹤声纹均值（enroll_all.npy）"""
import json, pathlib
import numpy as np

OUT = pathlib.Path(r"E:\RentAGirl\out")
rows = [json.loads(l) for l in (OUT / "chizuru_gold.jsonl").open(encoding="utf-8")]
by_ep = {}
for r in rows:
    by_ep.setdefault(r["ep"], []).append(r)

vecs = []
for ep, items in by_ep.items():
    emb = OUT / f"{ep}.lineemb.npy"
    if not emb.exists():
        print("missing", ep)
        continue
    E = np.load(emb)
    lines = json.loads((OUT / f"{ep}.asr.json").read_text(encoding="utf-8"))
    idx = {round(l["start"], 1): i for i, l in enumerate(lines)}
    for r in items:
        i = idx.get(round(r["start"], 1))
        if i is not None:
            vecs.append(E[i])

V = np.stack(vecs)
C = V.mean(axis=0)
C /= np.linalg.norm(C) + 1e-9
np.save(OUT / "enroll_all.npy", C)
print("enrolled", len(vecs), "lines from", len(by_ep), "episodes")
