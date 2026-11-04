import json, pathlib

OUT = pathlib.Path(r"E:\RentAGirl\out")
TAGS = {
    15: ("衝突", "high"),
    115: ("営業", "high"), 118: ("営業", "high"), 122: ("営業", "high"),
    196: ("素", "high"), 198: ("素", "high"), 200: ("素", "high"), 201: ("素", "high"),
    202: ("素", "high"), 203: ("素", "high"), 205: ("素", "high"), 206: ("素", "high"),
    222: ("素", "high"), 229: ("営業", "high"), 234: ("素", "med"),
    272: ("素", "med"),
    286: ("衝突", "high"), 289: ("衝突", "high"), 294: ("素", "high"),
    295: ("素", "high"), 297: ("素", "high"), 298: ("素", "high"), 300: ("素", "high"),
    301: ("素", "high"), 305: ("素", "high"),
    332: ("素", "med"), 344: ("素", "high"), 347: ("素", "high"), 349: ("素", "high"),
    350: ("素", "high"), 352: ("素", "high"), 354: ("素", "high"), 356: ("素", "high"),
    357: ("素", "high"), 360: ("衝突", "high"), 362: ("素", "high"), 364: ("素", "high"),
    366: ("素", "high"), 367: ("素", "high"), 377: ("素", "high"), 379: ("素", "high"),
    380: ("素", "high"), 381: ("素", "high"), 383: ("素", "high"), 389: ("素", "high"),
    395: ("素", "high"), 396: ("素", "high"),
}
lines = json.loads((OUT / "S01E10.asr.json").read_text(encoding="utf-8"))
zh = {}
p = OUT / "S01E10.jsonl"
if p.exists():
    for l in p.open(encoding="utf-8"):
        r = json.loads(l)
        if r.get("zh"):
            zh[round(r["start"], 1)] = r["zh"]
rows = []
for i, (mode, conf) in sorted(TAGS.items()):
    l = lines[i]
    rows.append({"ep": "S01E10", "idx": i, "start": l["start"], "end": l["end"],
                 "ja": l["ja"], "zh": zh.get(round(l["start"], 1), ""), "mode": mode, "conf": conf})
with open(OUT / "chizuru_gold_S01E10.jsonl", "w", encoding="utf-8") as f:
    for r in rows:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")
print("S01E10 gold:", len(rows))
