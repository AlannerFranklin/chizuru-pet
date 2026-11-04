import json, pathlib

OUT = pathlib.Path(r"E:\RentAGirl\out")
SEED = pathlib.Path(r"E:\test\rentagirl\work\chizuru_seed_v1.jsonl")

# 第 1 集的金标（之前手工标注，字段名不同）
ep1 = []
for l in SEED.open(encoding="utf-8"):
    r = json.loads(l)
    ep1.append({"ep": "S01E01", "idx": None, "start": r["ts"],
                "end": None, "ja": r["ja"], "zh": r.get("zh", ""),
                "mode": r["mode"], "conf": r["conf"]})

rows = ep1[:]
for f in sorted(OUT.glob("chizuru_gold_S*.jsonl")):
    rows += [json.loads(l) for l in f.open(encoding="utf-8")]

rows.sort(key=lambda r: (r["ep"], r["start"]))
with open(OUT / "chizuru_gold.jsonl", "w", encoding="utf-8") as f:
    for r in rows:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")

import collections
print("total", len(rows))
print("per ep:", dict(collections.Counter(r["ep"] for r in rows)))
print("per mode:", dict(collections.Counter(r["mode"] for r in rows)))
print("conf:", dict(collections.Counter(r["conf"] for r in rows)))
