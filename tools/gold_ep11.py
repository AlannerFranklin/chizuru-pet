import json, pathlib

OUT = pathlib.Path(r"E:\RentAGirl\out")
TAGS = {
    21: ("素", "high"), 22: ("素", "high"), 23: ("素", "high"), 24: ("素", "high"),
    25: ("素", "high"), 26: ("素", "high"), 28: ("素", "high"),
    204: ("素", "med"), 205: ("素", "high"),
    213: ("素", "high"), 215: ("素", "high"),
    270: ("素", "high"), 271: ("素", "high"), 272: ("素", "high"),
    279: ("素", "high"), 280: ("素", "high"), 281: ("素", "med"), 282: ("素", "high"),
    283: ("素", "high"), 284: ("素", "high"), 285: ("素", "high"), 286: ("素", "high"),
    287: ("素", "high"), 289: ("素", "high"), 290: ("素", "high"),
    295: ("素", "high"), 296: ("素", "high"), 297: ("素", "high"), 298: ("素", "high"),
    299: ("素", "high"),
    308: ("営業", "med"), 318: ("素", "med"), 319: ("営業", "high"),
    321: ("営業", "med"), 325: ("素", "med"),
}
lines = json.loads((OUT / "S01E11.asr.json").read_text(encoding="utf-8"))
zh = {}
p = OUT / "S01E11.jsonl"
if p.exists():
    for l in p.open(encoding="utf-8"):
        r = json.loads(l)
        if r.get("zh"):
            zh[round(r["start"], 1)] = r["zh"]
rows = []
for i, (mode, conf) in sorted(TAGS.items()):
    l = lines[i]
    rows.append({"ep": "S01E11", "idx": i, "start": l["start"], "end": l["end"],
                 "ja": l["ja"], "zh": zh.get(round(l["start"], 1), ""), "mode": mode, "conf": conf})
with open(OUT / "chizuru_gold_S01E11.jsonl", "w", encoding="utf-8") as f:
    for r in rows:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")
print("S01E11 gold:", len(rows))
