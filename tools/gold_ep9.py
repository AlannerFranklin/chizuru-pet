import json, pathlib

OUT = pathlib.Path(r"E:\RentAGirl\out")
TAGS = {
    21: ("営業", "high"), 23: ("素", "high"), 24: ("衝突", "high"),
    29: ("素", "high"), 30: ("素", "high"), 31: ("素", "high"), 32: ("素", "high"),
    33: ("素", "high"),
    120: ("素", "high"), 121: ("素", "high"), 123: ("営業", "high"),
    130: ("営業", "high"), 131: ("営業", "high"), 133: ("営業", "high"),
    148: ("衝突", "high"), 149: ("衝突", "high"), 152: ("衝突", "high"),
    155: ("衝突", "high"), 165: ("素", "med"),
    211: ("衝突", "high"),
    257: ("衝突", "high"), 259: ("衝突", "high"), 261: ("衝突", "high"),
    270: ("衝突", "high"), 271: ("衝突", "high"), 272: ("素", "high"),
    310: ("素", "med"), 316: ("営業", "high"), 321: ("営業", "high"),
    356: ("素", "med"),
}
lines = json.loads((OUT / "S01E09.asr.json").read_text(encoding="utf-8"))
zh = {}
p = OUT / "S01E09.jsonl"
if p.exists():
    for l in p.open(encoding="utf-8"):
        r = json.loads(l)
        if r.get("zh"):
            zh[round(r["start"], 1)] = r["zh"]
rows = []
for i, (mode, conf) in sorted(TAGS.items()):
    l = lines[i]
    rows.append({"ep": "S01E09", "idx": i, "start": l["start"], "end": l["end"],
                 "ja": l["ja"], "zh": zh.get(round(l["start"], 1), ""), "mode": mode, "conf": conf})
with open(OUT / "chizuru_gold_S01E09.jsonl", "w", encoding="utf-8") as f:
    for r in rows:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")
print("S01E09 gold:", len(rows))
