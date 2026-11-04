import json, pathlib
import numpy as np

REPO = pathlib.Path(r"E:\RentAGirl")
OUT = REPO / "out"

lines = [json.loads(l) for l in (OUT / "S01E01.spk.jsonl").open(encoding="utf-8")]
seeds = [json.loads(l) for l in open(r"E:\test\rentagirl\work\chizuru_seed_v1.jsonl", encoding="utf-8")]
asr = [json.loads(l) for l in open(r"E:\test\rentagirl\work\asr_ja.jsonl", encoding="utf-8")]
KAZUYA = [0, 2, 4, 6, 7, 13, 16, 26, 79, 83, 89, 148, 210, 211, 240, 241, 242, 243, 244,
          245, 246, 247, 248, 249, 250, 251, 252, 253, 254, 255, 256, 269, 279, 280, 281, 282, 283]

def near(ts, tol=1.2):
    return [l for l in lines if l["start"] - tol <= ts <= l["end"] + tol]

pos = [l for s in seeds if s["conf"] == "high" for l in near(s["ts"])]
neg = [l for i in KAZUYA if i < len(asr) for l in near(asr[i]["start"])]

p = np.array([l["chizuru_prob"] for l in pos])
n = np.array([l["chizuru_prob"] for l in neg])
print(f"pos lines={len(p)} mean={p.mean():.3f}  >0.5={np.mean(p>0.5):.2f}")
print(f"neg lines={len(n)} mean={n.mean():.3f}  >0.5={np.mean(n>0.5):.2f}")
for th in (0.5, 0.6, 0.7, 0.8, 0.9):
    tpr = float(np.mean(p > th)); fpr = float(np.mean(n > th))
    print(f"th={th}: recall={tpr:.2f} false_pos={fpr:.2f}")
