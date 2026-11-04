import json, pathlib

OUT = pathlib.Path(r"E:\RentAGirl\out")
TAGS = {
    69: ("素", "high"),
    75: ("衝突", "high"), 80: ("素", "high"), 81: ("素", "high"), 83: ("素", "high"),
    86: ("素", "high"), 87: ("素", "high"), 88: ("素", "high"),
    95: ("素", "high"), 96: ("素", "high"), 105: ("素", "high"),
    113: ("素", "high"), 114: ("素", "high"),
    125: ("软肋", "high"), 126: ("软肋", "high"), 127: ("软肋", "high"),
    128: ("软肋", "high"), 129: ("软肋", "high"), 130: ("软肋", "high"),
    132: ("软肋", "high"), 134: ("软肋", "high"), 135: ("软肋", "high"),
    136: ("软肋", "high"), 137: ("软肋", "high"), 138: ("软肋", "high"),
    140: ("软肋", "high"), 141: ("软肋", "high"), 142: ("软肋", "high"),
    143: ("软肋", "high"), 144: ("软肋", "high"), 145: ("软肋", "high"),
    147: ("素", "high"), 148: ("素", "high"),
    207: ("素", "high"), 209: ("素", "high"),
    251: ("素", "med"),
}
lines = json.loads((OUT / "S02E03.asr.json").read_text(encoding="utf-8"))
zh = {}
p = OUT / "S02E03.jsonl"
if p.exists():
    for l in p.open(encoding="utf-8"):
        r = json.loads(l)
        if r.get("zh"):
            zh[round(r["start"], 1)] = r["zh"]
rows = []
for i, (mode, conf) in sorted(TAGS.items()):
    l = lines[i]
    rows.append({"ep": "S02E03", "idx": i, "start": l["start"], "end": l["end"],
                 "ja": l["ja"], "zh": zh.get(round(l["start"], 1), ""), "mode": mode, "conf": conf})
with open(OUT / "chizuru_gold_S02E03.jsonl", "w", encoding="utf-8") as f:
    for r in rows:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")
print("S02E03 gold:", len(rows))
