import json, pathlib

OUT = pathlib.Path(r"E:\RentAGirl\out")

TAGS = {
    18: ("素", "high"), 19: ("素", "high"), 23: ("素", "med"), 24: ("素", "high"),
    26: ("素", "high"), 28: ("素", "med"), 31: ("素", "high"), 32: ("素", "high"),
    33: ("素", "high"), 35: ("素", "high"),
    39: ("素", "high"), 41: ("素", "high"), 49: ("素", "high"), 66: ("素", "high"),
    73: ("営業", "high"), 74: ("営業", "high"), 75: ("営業", "high"), 76: ("営業", "high"),
    77: ("営業", "high"), 78: ("営業", "high"),
    131: ("素", "high"), 132: ("営業", "high"),
    147: ("素", "high"), 148: ("素", "med"),
    154: ("素", "high"), 156: ("素", "high"), 158: ("素", "high"), 159: ("素", "high"),
    160: ("素", "high"), 161: ("素", "high"), 164: ("素", "high"), 165: ("素", "high"),
    166: ("素", "high"), 167: ("素", "high"),
    178: ("素", "high"), 179: ("素", "med"),
    200: ("素", "high"), 201: ("素", "high"), 202: ("素", "high"), 203: ("素", "high"),
    204: ("素", "high"), 205: ("素", "high"), 206: ("営業", "high"), 207: ("営業", "high"),
    211: ("素", "high"), 213: ("営業", "med"),
    245: ("営業", "high"), 278: ("素", "high"),
    348: ("衝突", "high"), 352: ("衝突", "high"), 353: ("衝突", "high"),
    356: ("衝突", "med"), 359: ("衝突", "med"), 361: ("衝突", "med"),
}

lines = json.loads((OUT / "S01E02.asr.json").read_text(encoding="utf-8"))
zh = {}
p = OUT / "S01E02.jsonl"
if p.exists():
    for l in p.open(encoding="utf-8"):
        r = json.loads(l)
        if r.get("zh"):
            zh[round(r["start"], 1)] = r["zh"]

rows = []
for i, (mode, conf) in sorted(TAGS.items()):
    l = lines[i]
    rows.append({"ep": "S01E02", "idx": i, "start": l["start"], "end": l["end"],
                 "ja": l["ja"], "zh": zh.get(round(l["start"], 1), ""), "mode": mode, "conf": conf})

with open(OUT / "chizuru_gold_S01E02.jsonl", "w", encoding="utf-8") as f:
    for r in rows:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")
print("S01E02 gold:", len(rows))
