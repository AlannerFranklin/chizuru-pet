import json, pathlib

OUT = pathlib.Path(r"E:\RentAGirl\out")

TAGS = {
    0: ("素", "med"),
    7: ("素", "high"), 9: ("素", "high"), 10: ("素", "high"), 11: ("素", "high"),
    12: ("素", "high"), 13: ("営業", "high"), 15: ("衝突", "high"),
    17: ("素", "high"), 18: ("素", "high"),
    45: ("素", "high"), 47: ("素", "high"),
    49: ("営業", "high"), 50: ("営業", "high"), 51: ("営業", "high"),
    52: ("素", "high"), 53: ("素", "high"), 54: ("素", "high"), 55: ("素", "high"),
    58: ("素", "high"), 59: ("素", "high"), 60: ("素", "high"),
    72: ("素", "high"),
    82: ("素", "high"), 83: ("素", "high"), 84: ("素", "high"), 85: ("営業", "high"),
    86: ("営業", "high"), 87: ("営業", "high"),
    94: ("素", "high"), 102: ("素", "high"), 106: ("素", "high"), 108: ("素", "high"),
    109: ("素", "high"), 111: ("素", "high"), 112: ("素", "high"), 115: ("素", "high"),
    141: ("素", "med"),
    197: ("素", "high"), 204: ("営業", "high"),
    230: ("素", "high"), 233: ("素", "high"), 234: ("素", "high"), 235: ("素", "high"),
    236: ("素", "high"), 241: ("衝突", "high"), 242: ("素", "high"), 243: ("素", "high"),
    244: ("素", "high"),
    260: ("衝突", "high"), 261: ("衝突", "high"), 264: ("衝突", "high"),
    267: ("素", "high"), 270: ("素", "high"), 271: ("素", "high"), 272: ("素", "high"),
    279: ("衝突", "high"), 280: ("営業", "high"), 284: ("衝突", "high"),
    292: ("素", "high"), 303: ("営業", "med"), 304: ("営業", "high"),
    340: ("衝突", "med"),
}

lines = json.loads((OUT / "S01E06.asr.json").read_text(encoding="utf-8"))
zh = {}
p = OUT / "S01E06.jsonl"
if p.exists():
    for l in p.open(encoding="utf-8"):
        r = json.loads(l)
        if r.get("zh"):
            zh[round(r["start"], 1)] = r["zh"]

rows = []
for i, (mode, conf) in sorted(TAGS.items()):
    l = lines[i]
    ja = l.get("ja") or l.get("text", "")
    rows.append({"ep": "S01E06", "idx": i, "start": l["start"], "end": l["end"],
                 "ja": ja, "zh": zh.get(round(l["start"], 1), ""), "mode": mode, "conf": conf})

with open(OUT / "chizuru_gold_S01E06.jsonl", "w", encoding="utf-8") as f:
    for r in rows:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")
print("S01E06 gold:", len(rows))
