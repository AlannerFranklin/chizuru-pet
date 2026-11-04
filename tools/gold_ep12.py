import json, pathlib

OUT = pathlib.Path(r"E:\RentAGirl\out")
TAGS = {
    0: ("素", "high"), 6: ("素", "high"), 35: ("素", "high"),
    45: ("営業", "high"), 49: ("営業", "med"),
    58: ("営業", "high"), 59: ("営業", "high"), 63: ("素", "high"), 64: ("素", "med"),
    67: ("素", "high"), 68: ("素", "high"), 69: ("素", "high"),
    91: ("素", "high"), 95: ("衝突", "high"), 96: ("営業", "high"),
    120: ("素", "high"), 123: ("素", "high"),
    214: ("衝突", "high"), 215: ("衝突", "high"),
    229: ("素", "high"), 230: ("素", "high"), 231: ("素", "high"), 232: ("素", "high"),
    234: ("素", "high"),
    240: ("素", "high"), 241: ("素", "high"),
    249: ("素", "high"), 250: ("素", "high"), 254: ("素", "high"), 255: ("素", "high"),
    264: ("素", "med"), 265: ("衝突", "high"), 267: ("素", "med"),
    268: ("素", "high"), 269: ("素", "high"),
}
lines = json.loads((OUT / "S01E12.asr.json").read_text(encoding="utf-8"))
zh = {}
p = OUT / "S01E12.jsonl"
if p.exists():
    for l in p.open(encoding="utf-8"):
        r = json.loads(l)
        if r.get("zh"):
            zh[round(r["start"], 1)] = r["zh"]
rows = []
for i, (mode, conf) in sorted(TAGS.items()):
    l = lines[i]
    rows.append({"ep": "S01E12", "idx": i, "start": l["start"], "end": l["end"],
                 "ja": l["ja"], "zh": zh.get(round(l["start"], 1), ""), "mode": mode, "conf": conf})
with open(OUT / "chizuru_gold_S01E12.jsonl", "w", encoding="utf-8") as f:
    for r in rows:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")
print("S01E12 gold:", len(rows))
