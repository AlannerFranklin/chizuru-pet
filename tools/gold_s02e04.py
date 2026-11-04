import json, pathlib

OUT = pathlib.Path(r"E:\RentAGirl\out")
TAGS = {
    77: ("営業", "high"), 78: ("営業", "high"), 81: ("営業", "high"),
    98: ("素", "high"), 318: ("素", "high"),
}
lines = json.loads((OUT / "S02E04.asr.json").read_text(encoding="utf-8"))
zh = {}
p = OUT / "S02E04.jsonl"
if p.exists():
    for l in p.open(encoding="utf-8"):
        r = json.loads(l)
        if r.get("zh"):
            zh[round(r["start"], 1)] = r["zh"]
rows = []
for i, (mode, conf) in sorted(TAGS.items()):
    l = lines[i]
    rows.append({"ep": "S02E04", "idx": i, "start": l["start"], "end": l["end"],
                 "ja": l["ja"], "zh": zh.get(round(l["start"], 1), ""), "mode": mode, "conf": conf})
with open(OUT / "chizuru_gold_S02E04.jsonl", "w", encoding="utf-8") as f:
    for r in rows:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")
print("S02E04 gold:", len(rows))
