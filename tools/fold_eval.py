"""6 折交叉验证：每次用 5 集金标当声纹参照，测剩下 1 集。
分数 = w*line_sim + (1-w)*cluster_sim（cluster 来自 pyannote）
输出各阈值下的 P/R，并给出「精确率 >= 0.9 时能覆盖多少」。
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
W_CLUSTER = 0.75   # 0.75*line_sim + 0.25*cluster_sim（沿用上次调参结果的方向）


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


def ov(a, b, c, d):
    return max(0.0, min(b, d) - max(a, c))


def load_ep(ep):
    cache = OUT / f"{ep}.lineemb.npy"
    lines = json.loads((OUT / f"{ep}.asr.json").read_text(encoding="utf-8"))
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
        print(f"{ep}: embedded {len(E)}", flush=True)
    gt = gold_ts(ep)
    gold = np.array([1 if any(abs(l["start"] - t) <= 0.6 for t in gt) else 0 for l in lines])
    # 聚类相似度
    diar_p = OUT / f"{ep}.pydiar.json"
    cs = np.full(len(lines), -1.0)
    if diar_p.exists():
        diar = json.loads(diar_p.read_text(encoding="utf-8"))
        spk = []
        for l in lines:
            best, bov = None, 0.0
            for x, y, c in diar:
                o = ov(l["start"], l["end"], x, y)
                if o > bov:
                    best, bov = c, o
            spk.append(best)
        # 先算临时 line sim（用本集金标算不了，留到折内）
        cs = np.array(spk, dtype=object)
    return lines, E, gold, cs


def main():
    data = {ep: load_ep(ep) for ep in EPS}
    print("\n=== 6-fold (enroll on 5, test on 1) ===", flush=True)
    allp, allr = [], []
    for test in EPS:
        train = [e for e in EPS if e != test]
        # 参照向量
        vecs = []
        for e in train:
            lines, E, gold, cs = data[e]
            vecs.append(E[gold == 1])
        C = np.mean(np.vstack(vecs), axis=0)
        C /= (np.linalg.norm(C) + 1e-9)

        lines, E, gold, cs = data[test]
        line_sim = E @ C
        # 簇相似度 = 簇内中位数
        cluster_sim = {}
        if cs.dtype == object:
            for s in set(cs):
                vals = [line_sim[i] for i in range(len(lines)) if cs[i] == s]
                if vals:
                    cluster_sim[s] = float(np.median(vals))
            csim = np.array([cluster_sim.get(s, -1.0) for s in cs])
        else:
            csim = cs
        score = W_CLUSTER * line_sim + (1 - W_CLUSTER) * csim

        row = []
        for th in (0.45, 0.50, 0.55, 0.60, 0.65, 0.70):
            pred = score >= th
            tp = int((pred & (gold == 1)).sum()); fp = int((pred & (gold == 0)).sum())
            fn = int(((~pred) & (gold == 1)).sum())
            p = tp / (tp + fp) if tp + fp else 0
            r = tp / (tp + fn) if tp + fn else 0
            row.append(f"th{th:.2f}:P{p:.2f}/R{r:.2f}")
        print(f"{test}: " + "  ".join(row), flush=True)

        # 汇总（用 th=0.60）
        pred = score >= 0.60
        tp = int((pred & (gold == 1)).sum()); fp = int((pred & (gold == 0)).sum())
        fn = int(((~pred) & (gold == 1)).sum())
        allp.append(tp / (tp + fp) if tp + fp else 0)
        allr.append(tp / (tp + fn) if tp + fn else 0)

    print(f"\nAVG @th0.60: P={np.mean(allp):.2f} R={np.mean(allr):.2f}", flush=True)


if __name__ == "__main__":
    main()
