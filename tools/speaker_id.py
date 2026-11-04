"""用第 1 集人工标注做种子，训练「这句是不是千鹤」的分类器，再对全剧逐行打分。
特征 = ECAPA 声纹(192) + 基频 F0（男女声强区分）。
输出 out\\<ep>.spk.jsonl
用法:
  python speaker_id.py --train
  python speaker_id.py --apply
"""
import argparse, json, pathlib, pickle, time
import numpy as np

REPO = pathlib.Path(r"E:\RentAGirl")
OUT = REPO / "out"
RAW = REPO / "raw"
LOCAL = pathlib.Path(r"E:\test\rentagirl\models\ecapa")
SR = 16000
MODEL_PKL = OUT / "spk_model.pkl"

KAZUYA_IDX = [0, 2, 4, 6, 7, 13, 16, 26, 79, 83, 89, 148, 210, 211, 240, 241, 242,
              243, 244, 245, 246, 247, 248, 249, 250, 251, 252, 253, 254, 255, 256,
              269, 279, 280, 281, 282, 283]


def load_ecapa():
    import speechbrain.utils.parameter_transfer as PT
    import speechbrain.utils.fetching as FETCH

    def _local_fetch(filename, source, savedir, **kwargs):
        for cand in (pathlib.Path(savedir) / filename, LOCAL / filename, pathlib.Path(source) / filename):
            if cand.exists():
                return cand
        raise FileNotFoundError(filename)

    PT.fetch = _local_fetch
    FETCH.fetch = _local_fetch
    from speechbrain.inference.speaker import EncoderClassifier
    return EncoderClassifier.from_hparams(source=str(LOCAL), savedir=str(LOCAL), run_opts={"device": "cpu"})


def f0_median(a, fmin=70, fmax=400):
    a = np.asarray(a, dtype=np.float64)
    a = a - a.mean()
    if a.size < SR * 0.3 or np.abs(a).max() < 1e-4:
        return 0.0
    frame, hop = int(0.04 * SR), int(0.02 * SR)
    lmin, lmax = int(SR / fmax), int(SR / fmin)
    vals = []
    for st in range(0, a.size - frame, hop):
        x = a[st:st + frame]
        if np.sqrt((x ** 2).mean()) < 0.01:
            continue
        x = x * np.hamming(frame)
        ac = np.correlate(x, x, mode="full")[frame - 1:]
        if ac[0] <= 0:
            continue
        ac = ac / ac[0]
        seg = ac[lmin:lmax]
        if seg.size == 0:
            continue
        peak = seg.max()
        if peak < 0.3:
            continue
        cand = np.where((seg[1:-1] > seg[:-2]) & (seg[1:-1] >= seg[2:]) & (seg[1:-1] > 0.85 * peak))[0] + 1
        if cand.size == 0:
            continue
        vals.append(SR / (cand[0] + lmin))
    return float(np.median(vals)) if vals else 0.0


def features(clf, wav):
    import torch
    if wav.size < int(0.6 * SR):
        wav = np.pad(wav, (0, int(0.6 * SR) - wav.size))
    if wav.size > 6 * SR:
        wav = wav[: 6 * SR]
    with torch.no_grad():
        e = clf.encode_batch(torch.from_numpy(wav.astype(np.float32)).unsqueeze(0)).squeeze().cpu().numpy()
    e = e / (np.linalg.norm(e) + 1e-9)
    f0 = f0_median(wav)
    extra = np.array([f0 / 300.0, 1.0 if f0 > 190 else 0.0, 1.0 if f0 <= 0 else 0.0])
    return np.concatenate([e, extra])


def line_audio(audio, line, pad=0.15):
    a = int(max(0, line["start"] - pad) * SR)
    b = int(min(len(audio) / SR, line["end"] + pad) * SR)
    return audio[a:b]


def train():
    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import cross_val_score
    from process_episode import decode

    ep1 = [json.loads(l) for l in (OUT / "S01E01.jsonl").open(encoding="utf-8")]
    seeds = [json.loads(l) for l in open(r"E:\test\rentagirl\work\chizuru_seed_v1.jsonl", encoding="utf-8")]
    asr = [json.loads(l) for l in open(r"E:\test\rentagirl\work\asr_ja.jsonl", encoding="utf-8")]
    pos_ts = [s["ts"] for s in seeds if s["conf"] == "high"]
    neg_ts = [asr[i]["start"] for i in KAZUYA_IDX if i < len(asr)]

    audio = decode(RAW / "S01E01.mp4", 1468.5)
    clf = load_ecapa()

    def near(ts):
        return [l for l in ep1 if l["start"] - 0.4 <= ts <= l["end"] + 0.9]

    X, y = [], []
    for ts in pos_ts:
        for l in near(ts):
            X.append(features(clf, line_audio(audio, l))); y.append(1)
    for ts in neg_ts:
        for l in near(ts):
            X.append(features(clf, line_audio(audio, l))); y.append(0)
    X = np.stack(X); y = np.array(y)
    print("samples", X.shape, "pos", int(y.sum()), "neg", int((1 - y).sum()))
    lr = LogisticRegression(C=0.5, max_iter=3000)
    cv = cross_val_score(lr, X, y, cv=5)
    print(f"cv acc = {cv.mean():.3f} (+-{cv.std():.3f})")
    lr.fit(X, y)
    pickle.dump(lr, open(MODEL_PKL, "wb"))
    print("saved", MODEL_PKL)


def apply_all(limit=None):
    from process_episode import decode
    lr = pickle.load(open(MODEL_PKL, "rb"))
    clf = load_ecapa()
    eps = sorted(p.stem.replace(".asr", "") for p in OUT.glob("S*E*.asr.json"))
    if limit:
        eps = eps[:limit]
    todo = [e for e in eps if not (OUT / f"{e}.spk.jsonl").exists()]
    print(f"{len(todo)} episodes to score", flush=True)
    for ep in todo:
        t0 = time.time()
        lines = json.loads((OUT / f"{ep}.asr.json").read_text(encoding="utf-8"))
        cut = json.loads((OUT / f"{ep}.cut.json").read_text(encoding="utf-8"))["cut_s"]
        audio = decode(RAW / f"{ep}.mp4", cut)
        probs = []
        for l in lines:
            probs.append(float(lr.predict_proba(features(clf, line_audio(audio, l)).reshape(1, -1))[0, 1]))
        # 时间平滑：相邻 5 行取中位数，避免孤立的跳变
        arr = np.array(probs)
        if len(arr) >= 5:
            sm = np.array([np.median(arr[max(0, i - 2):i + 3]) for i in range(len(arr))])
        else:
            sm = arr
        with open(OUT / f"{ep}.spk.jsonl", "w", encoding="utf-8") as g:
            for l, p, s in zip(lines, arr, sm):
                g.write(json.dumps({**l, "chizuru_prob": round(float(p), 3),
                                    "chizuru_prob_smooth": round(float(s), 3)}, ensure_ascii=False) + "\n")
        n = int((sm >= 0.6).sum())
        print(f"{ep}: {n}/{len(lines)} chizuru, {time.time()-t0:.0f}s", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--train", action="store_true")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--limit", type=int, default=None)
    args = ap.parse_args()
    if args.train:
        train()
    if args.apply:
        apply_all(args.limit)


if __name__ == "__main__":
    main()
