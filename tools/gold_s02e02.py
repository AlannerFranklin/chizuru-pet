import json, pathlib

OUT = pathlib.Path(r"E:\RentAGirl\out")
TAGS = {
    28: ("営業", "high"), 29: ("営業", "high"), 33: ("素", "high"),
    34: ("素", "high"), 35: ("営業", "high"), 36: ("素", "high"), 37: ("素", "high"),
    38: ("素", "high"), 39: ("素", "high"), 40: ("素", "high"), 41: ("素", "high"),
    45: ("素", "high"), 46: ("素", "high"),
    50: ("素", "high"), 52: ("素", "high"), 53: ("素", "high"), 54: ("素", "high"),
    57: ("衝突", "high"), 87: ("素", "high"),
    94: ("素", "high"),
    102: ("素", "high"), 103: ("素", "high"), 104: ("素", "high"), 107: ("素", "high"),
    108: ("素", "high"), 109: ("素", "high"), 110: ("素", "med"),
    122: ("素", "high"), 124: ("素", "high"), 125: ("素", "high"),
    144: ("素", "high"), 145: ("素", "high"), 146: ("素", "high"), 147: ("素", "high"),
    163: ("素", "high"), 164: ("素", "high"), 165: ("素", "high"),
    169: ("素", "high"), 170: ("素", "high"), 172: ("素", "high"), 173: ("素", "high"),
    174: ("素", "high"), 175: ("素", "high"),
    182: ("素", "high"), 185: ("素", "high"), 186: ("素", "high"), 187: ("素", "high"),
    198: ("素", "high"), 204: ("衝突", "high"), 210: ("素", "high"),
    276: ("素", "high"), 277: ("素", "high"), 292: ("素", "med"),
}
lines = json.loads((OUT / "S02E02.asr.json").read_text(encoding="utf-8"))
zh = {}
p = OUT / "S02E02.jsonl"
if p.exists():
    for l in p.open(encoding="utf-8"):
        r = json.loads(l)
        if r.get("zh"):
            zh[round(r["start"], 1)] = r["zh"]
rows = []
for i, (mode, conf) in sorted(TAGS.items()):
    l = lines[i]
    rows.append({"ep": "S02E02", "idx": i, "start": l["start"], "end": l["end"],
                 "ja": l["ja"], "zh": zh.get(round(l["start"], 1), ""), "mode": mode, "conf": conf})
with open(OUT / "chizuru_gold_S02E02.jsonl", "w", encoding="utf-8") as f:
    for r in rows:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")
print("S02E02 gold:", len(rows))
