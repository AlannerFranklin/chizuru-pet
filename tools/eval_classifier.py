"""把人工金标当训练/测试集，检验「能否自动分出千鹤的行」。
特征：ECAPA 声纹 + F0（中位数/高低比）+ 日文男女语体标记
评估：留一集交叉验证（train on 5 eps, test on 1）
"""
import json, pathlib, sys
import numpy as np

REPO = pathlib.Path(r"E:\RentAGirl")
OUT = REPO / "out"
sys.path.insert(0, str(REPO / "tools"))

from speaker_id import load_ecapa, f0_median, line_audio
from process_episode import decode

EPS = ["S01E01", "S01E03", "S01E04", "S01E05", "S01E06", "S01E07"]
SR = 16000

MALE = ["俺", "おれ", "僕", "ぼく", "だぜ", "かよ", "んだよ", "じゃねえ", "すんのか",
        "やめろ", "だろ", "なんだよ", "お前", "てめえ", "ふざけんな"]
FEMALE = ["わよ", "のよ", "じゃん", "でしょ", "かしら", "わね", "なのよ", "あたし", "だわ"]
POLITE = ["です", "ます"]


def text_feats(ja):
    m = sum(ja.count(w) for w in MALE)
    f = sum(ja.count(w) for w in FEMALE)
    p = sum(ja.count(w) for w in POLITE)
    return np.array([m, f, p, len(ja) / 20.0, 1.0 if m else 0.0, 1.0 if f else 0.0])


def gold_map(ep):
    """把金标行映射到 asr 行的 index（时间重叠即算）"""
    gold = [json.loads(l) for l in (OUT / "chizuru_gold.jsonl").open(encoding="utf-8")]
    lines = json.loads((OUT / f"{ep}.asr.json").read_text(encoding="utf-8"))
    idx = set()
    for g in gold:
        if g["ep"] != ep:
            continue
        for i, l in enumerate(lines):
            if l["start"] <= g["start"] + 0.3 and l["end"] >= g["start"] - 0.3:
                idx.add(i)
                break
    return lines, idx


def main():
    clf = load_ecapa()
    data = {}
    for ep in EPS:
        lines, gold_idx = gold_map(ep)
        cut = json.loads((OUT / f"{ep}.cut.json").read_text(encoding="utf-8"))["cut_s"]
        audio = decode(REPO / "raw" / f"{ep}.mp4", cut)
        X, y = [], []
        for i, l in enumerate(lines):
            w = line_audio(audio, l)
            e = np.concatenate([
                __import__("speaker_id").features(clf, w)[:192],
                text_feats(l.get("ja") or l.get("text", "")),
                [f0_median(w) / 300.0],
            ])
            X.append(e)
            y.append(1 if i in gold_idx else 0)
        data[ep] = (np.stack(X), np.array(y))
        print(f"{ep}: lines={len(y)} gold={int(np.array(y).sum())}", flush=True)

    from sklearn.linear_model import LogisticRegression
    print("\n=== leave-one-episode-out ===", flush=True)
    for test in EPS:
        Xtr = np.vstack([data[e][0] for e in EPS if e != test])
        ytr = np.concatenate([data[e][1] for e in EPS if e != test])
        Xte, yte = data[test]
        lr = LogisticRegression(C=0.3, max_iter=3000, class_weight="balanced")
        lr.fit(Xtr, ytr)
        p = lr.predict_proba(Xte)[:, 1]
        for th in (0.4, 0.5, 0.6):
            pred = p >= th
            tp = int(((pred == 1) & (yte == 1)).sum())
            fp = int(((pred == 1) & (yte == 0)).sum())
            fn = int(((pred == 0) & (yte == 1)).sum())
            prec = tp / (tp + fp) if tp + fp else 0
            rec = tp / (tp + fn) if tp + fn else 0
            print(f"  {test} th={th}: P={prec:.2f} R={rec:.2f} (tp={tp} fp={fp} fn={fn})", flush=True)


if __name__ == "__main__":
    main()
