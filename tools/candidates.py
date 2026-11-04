"""生成「千鹤候选行」清单：用其余 6 集金标做声纹参照，逐行打分。
用法: python candidates.py S01E02 [threshold]
输出: out/<ep>_cand.txt
"""
import json, pathlib, sys
import numpy as np
import torch

REPO = pathlib.Path(r"E:\RentAGirl")
OUT = REPO / "out"
BASE = pathlib.Path(r"E:\test\pyannote")
sys.path.insert(0, str(REPO / "tools"))
from process_episode import decode
from pyannote.audio import Model

EMB = Model.from_pretrained(str(BASE / "emb"))
SR = 16000
EPS = ["S01E01", "S01E03", "S01E04", "S01E05", "S01E06", "S01E07"]


def embed(wav):
    if len(wav) < int(0.5 * SR):
        wav = np.pad(wav, (0, int(0.5 * SR) - len(wav)))
    w = torch.from_numpy(wav.astype(np.float32)).unsqueeze(0).unsqueeze(0)
    with torch.no_grad():
        e = EMB(w).squeeze().cpu().numpy()
    return e / (np.linalg.norm(e) + 1e-9)


def gold_ts(ep):
    rows = [json.loads(l) for l in (OUT / "chizuru_gold.jsonl").open(encoding="utf-8")]
    return [r["start"] for r in rows if r["ep"] == ep]


def enroll():
    cache = OUT / "enroll_all.npy"
    if cache.exists():
        return np.load(cache)
    vecs = []
    for ep in EPS:
        e_cache = OUT / f"{ep}.lineemb.npy"
        E = np.load(e_cache)
        lines = json.loads((OUT / f"{ep}.asr.json").read_text(encoding="utf-8"))
        gt = gold_ts(ep)
        mask = np.array([1 if any(abs(l["start"] - t) <= 0.6 for t in gt) else 0 for l in lines])
        vecs.append(E[mask == 1])
    C = np.mean(np.vstack(vecs), axis=0)
    C /= np.linalg.norm(C) + 1e-9
    np.save(cache, C)
    return C


def main():
    ep = sys.argv[1]
    th = float(sys.argv[2]) if len(sys.argv) > 2 else 0.45
    C = enroll()
    lines = json.loads((OUT / f"{ep}.asr.json").read_text(encoding="utf-8"))
    cache = OUT / f"{ep}.lineemb.npy"
    if cache.exists():
        E = np.load(cache)
    else:
        cut = json.loads((OUT / f"{ep}.cut.json").read_text(encoding="utf-8"))["cut_s"]
        audio = decode(REPO / "raw" / f"{ep}.mp4", cut)
        vecs = []
        for l in lines:
            a = audio[int(l["start"] * SR): int(l["end"] * SR)]
            vecs.append(embed(a) if len(a) > SR * 0.4 else np.zeros(256))
        E = np.stack(vecs)
        np.save(cache, E)

    sims = E @ C
    zh = {}
    p = OUT / f"{ep}.jsonl"
    if p.exists():
        for l in p.open(encoding="utf-8"):
            r = json.loads(l)
            if r.get("zh"):
                zh[round(r["start"], 1)] = r["zh"]

    out = []
    for i, l in enumerate(lines):
        if sims[i] >= th:
            z = zh.get(round(l["start"], 1), "")
            ja = l["ja"]
            flag = ""
            if "カズヤさん" in ja or "カズ君" in ja:
                flag = "  <<瑠夏?"
            elif "あたし" in ja:
                flag = "  <<麻美?"
            out.append(f"{i:03d} {l['start']:7.1f} {sims[i]:.2f} {ja}" + (f"  || {z}" if z else "") + flag)
    (OUT / f"{ep}_cand.txt").write_text("\n".join(out), encoding="utf-8")
    print(f"{ep}: {len(out)} candidates out of {len(lines)} (th={th})")


if __name__ == "__main__":
    main()
