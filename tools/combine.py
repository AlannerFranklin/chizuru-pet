"""合并方案：pyannote 聚类 + 声纹注册相似度。
对每一行：
  line_sim  = 与千鹤声纹均值的余弦相似度
  cluster_sim = 该行所属聚类中心的相似度
  score = w*line_sim + (1-w)*cluster_sim
调参集: S01E06，测试集: S01E07
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
C = np.load(OUT / "chizuru_enroll.npy")


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


def prepare(ep):
    lines = json.loads((OUT / f"{ep}.asr.json").read_text(encoding="utf-8"))
    diar = json.loads((OUT / f"{ep}.pydiar.json").read_text(encoding="utf-8"))
    cut = json.loads((OUT / f"{ep}.cut.json").read_text(encoding="utf-8"))["cut_s"]
    audio = decode(REPO / "raw" / f"{ep}.mp4", cut)
    gt = gold_ts(ep)

    spk, sims = [], []
    for l in lines:
        a = audio[int(l["start"] * SR): int(l["end"] * SR)]
        sims.append(float(embed(a) @ C) if len(a) > SR * 0.4 else -1.0)
        best, bov = None, 0.0
        for x, y, c in diar:
            o = ov(l["start"], l["end"], x, y)
            if o > bov:
                best, bov = c, o
        spk.append(best)

    # 每个聚类中心 = 该簇所有行声纹的均值（用行 sim 的向量不精确，这里用均值相似度的近似：
    # 重新计算簇内平均 embedding 太贵，这里用簇内 line_sim 的中位数当簇相似度）
    cluster_sim = {}
    for s in set(spk):
        vals = [sims[i] for i in range(len(lines)) if spk[i] == s]
        if vals:
            cluster_sim[s] = float(np.median(vals))

    gold = np.array([1 if any(abs(l["start"] - t) <= 0.6 for t in gt) else 0 for l in lines])
    return np.array(sims), np.array([cluster_sim.get(s, -1.0) for s in spk]), gold


def score_curve(ls, cs, w):
    return w * ls + (1 - w) * cs


def best_threshold(s, y):
    best = (-1, 0, 0, 0)
    for th in np.arange(-0.1, 0.9, 0.01):
        pred = s >= th
        tp = int((pred & (y == 1)).sum()); fp = int((pred & (y == 0)).sum())
        fn = int(((~pred) & (y == 1)).sum())
        p = tp / (tp + fp) if tp + fp else 0
        r = tp / (tp + fn) if tp + fn else 0
        f1 = 2 * p * r / (p + r) if p + r else 0
        if f1 > best[0]:
            best = (f1, th, p, r)
    return best


def main():
    dev = prepare("S01E06")
    test = prepare("S01E07")
    best = None
    for w in (0.0, 0.25, 0.5, 0.75, 1.0):
        s = score_curve(*dev[:2], w)
        f1, th, p, r = best_threshold(s, dev[2])
        if best is None or f1 > best[0]:
            best = (f1, w, th, p, r)
        print(f"dev w={w:.2f} th={th:.2f} F1={f1:.2f} P={p:.2f} R={r:.2f}", flush=True)
    f1, w, th, p, r = best
    print(f"\nchosen w={w} th={th:.2f} (dev F1={f1:.2f})", flush=True)
    s = score_curve(*test[:2], w)
    f1t, tht, pt, rt = best_threshold(s, test[2])
    print(f"TEST S01E07: F1={f1t:.2f} P={pt:.2f} R={rt:.2f} (at th={tht:.2f})", flush=True)
    # 用 dev 的阈值直接套测试集，更诚实的数字
    pred = s >= th
    tp = int((pred & (test[2] == 1)).sum()); fp = int((pred & (test[2] == 0)).sum())
    fn = int(((~pred) & (test[2] == 1)).sum())
    p2 = tp / (tp + fp) if tp + fp else 0
    r2 = tp / (tp + fn) if tp + fn else 0
    f2 = 2 * p2 * r2 / (p2 + r2) if p2 + r2 else 0
    print(f"TEST S01E07 @dev-th={th:.2f}: P={p2:.2f} R={r2:.2f} F1={f2:.2f}", flush=True)


if __name__ == "__main__":
    main()
