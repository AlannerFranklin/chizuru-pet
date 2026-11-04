"""声纹注册法：用其它集的千鹤金标当参考，对目标集逐行打分（相似度）。
这比聚类更贴近产品做法——用户标几十句，系统匹配其余。
用法: python eval_enroll.py S01E06 S01E07
"""
import json, pathlib, sys
import numpy as np
import soundfile as sf, torch

REPO = pathlib.Path(r"E:\RentAGirl")
OUT = REPO / "out"
BASE = pathlib.Path(r"E:\test\pyannote")
sys.path.insert(0, str(REPO / "tools"))
from process_episode import decode
from pyannote.audio import Model

EMB = Model.from_pretrained(str(BASE / "emb"))
SR = 16000


def embed(wav):
    if len(wav) < int(0.5 * SR):
        wav = np.pad(wav, (0, int(0.5 * SR) - len(wav)))
    w = torch.from_numpy(wav.astype(np.float32)).unsqueeze(0).unsqueeze(0)
    with torch.no_grad():
        e = EMB(w).squeeze().cpu().numpy()
    return e / (np.linalg.norm(e) + 1e-9)


def load(ep):
    lines = json.loads((OUT / f"{ep}.asr.json").read_text(encoding="utf-8"))
    cut = json.loads((OUT / f"{ep}.cut.json").read_text(encoding="utf-8"))["cut_s"]
    audio = decode(REPO / "raw" / f"{ep}.mp4", cut)
    return lines, audio


def gold_ts(ep):
    rows = [json.loads(l) for l in (OUT / "chizuru_gold.jsonl").open(encoding="utf-8")]
    return [r["start"] for r in rows if r["ep"] == ep]


def main():
    test_eps = sys.argv[1:] or ["S01E06", "S01E07"]
    train_eps = ["S01E01", "S01E03", "S01E04", "S01E05"]

    vecs = []
    for ep in train_eps:
        lines, audio = load(ep)
        gt = gold_ts(ep)
        for l in lines:
            if any(abs(l["start"] - t) <= 0.6 for t in gt):
                a = audio[int(l["start"] * SR): int(l["end"] * SR)]
                if len(a) > SR * 0.5:
                    vecs.append(embed(a))
        print(f"{ep}: enrolled {len(vecs)} so far", flush=True)

    C = np.mean(vecs, axis=0)
    C /= np.linalg.norm(C)
    np.save(OUT / "chizuru_enroll.npy", C)
    print(f"enrolled {len(vecs)} gold lines", flush=True)

    for ep in test_eps:
        lines, audio = load(ep)
        gt = gold_ts(ep)
        scores, gold = [], []
        for l in lines:
            a = audio[int(l["start"] * SR): int(l["end"] * SR)]
            if len(a) < SR * 0.5:
                scores.append(-1.0)
            else:
                scores.append(float(embed(a) @ C))
            gold.append(1 if any(abs(l["start"] - t) <= 0.6 for t in gt) else 0)
        scores = np.array(scores); gold = np.array(gold)
        best = None
        for th in np.arange(0.2, 0.75, 0.02):
            pred = scores >= th
            tp = int((pred & (gold == 1)).sum()); fp = int((pred & (gold == 0)).sum())
            fn = int(((~pred) & (gold == 1)).sum())
            p = tp / (tp + fp) if tp + fp else 0
            r = tp / (tp + fn) if tp + fn else 0
            f1 = 2 * p * r / (p + r) if p + r else 0
            if best is None or f1 > best[0]:
                best = (f1, th, p, r)
        print(f"{ep}: best F1={best[0]:.2f} at th={best[1]:.2f} P={best[2]:.2f} R={best[3]:.2f}", flush=True)


if __name__ == "__main__":
    main()
