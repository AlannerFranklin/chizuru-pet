import json, pathlib
import numpy as np

REPO = pathlib.Path(r"E:\RentAGirl")
OUT = REPO / "out"
RAW = REPO / "raw"
SR = 16000

import sys
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from speaker_id import load_ecapa, f0_median, features, line_audio
from process_episode import decode

ep1 = json.loads((OUT / "S01E01.asr.json").read_text(encoding="utf-8"))
seeds = [json.loads(l) for l in open(r"E:\test\rentagirl\work\chizuru_seed_v1.jsonl", encoding="utf-8")]
asr = [json.loads(l) for l in open(r"E:\test\rentagirl\work\asr_ja.jsonl", encoding="utf-8")]
KAZUYA = [0, 2, 4, 6, 7, 13, 16, 26, 79, 83, 89, 148, 210, 211, 240, 241, 242, 243, 244,
          245, 246, 247, 248, 249, 250, 251, 252, 253, 254, 255, 256, 269, 279, 280, 281, 282, 283]

audio = decode(RAW / "S01E01.mp4", 1468.5)
clf = load_ecapa()

pos_ts = [s["ts"] for s in seeds if s["conf"] == "high"]
neg_ts = [asr[i]["start"] for i in KAZUYA if i < len(asr)]

def near(ts):
    return [l for l in ep1 if l["start"] - 0.4 <= ts <= l["end"] + 0.9]

def stats(name, lines):
    f0s, sims = [], []
    for l in lines:
        w = line_audio(audio, l)
        f0s.append(f0_median(w))
        e = features(clf, w)[:192]
        sims.append(float(e @ np.load(OUT / "seed_centroid.npy")))
    f0s = np.array(f0s); sims = np.array(sims)
    print(f"{name}: n={len(f0s)} f0_med={np.median(f0s):.0f} "
          f"f0>190={np.mean(f0s > 190):.2f} sim_mean={sims.mean():.3f}")

# 先算种子质心
if not (OUT / "seed_centroid.npy").exists():
    vecs = []
    for ts in pos_ts:
        for l in near(ts):
            vecs.append(features(clf, line_audio(audio, l))[:192])
    c = np.mean(vecs, axis=0); c /= np.linalg.norm(c)
    np.save(OUT / "seed_centroid.npy", c)

pos_lines = [l for ts in pos_ts for l in near(ts)]
neg_lines = [l for ts in neg_ts for l in near(ts)]
stats("pos(千鹤)", pos_lines)
stats("neg(和也)", neg_lines)
