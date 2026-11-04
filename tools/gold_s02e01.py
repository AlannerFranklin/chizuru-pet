import json, pathlib

OUT = pathlib.Path(r"E:\RentAGirl\out")
TAGS = {
    26: ("素", "high"), 27: ("素", "high"), 28: ("素", "high"), 29: ("素", "high"),
    30: ("素", "high"), 31: ("素", "high"), 32: ("素", "high"), 33: ("素", "high"),
    34: ("素", "high"), 35: ("素", "high"), 36: ("素", "high"),
    54: ("素", "high"), 55: ("素", "high"),
    79: ("素", "high"), 80: ("素", "high"),
    184: ("素", "high"), 185: ("素", "high"),
    201: ("衝突", "high"), 203: ("衝突", "high"), 204: ("素", "high"), 205: ("素", "high"),
    211: ("衝突", "high"),
    227: ("素", "high"), 228: ("素", "high"),
    235: ("素", "high"), 236: ("素", "high"), 237: ("素", "high"), 238: ("素", "high"),
    239: ("素", "high"), 240: ("素", "high"), 242: ("素", "high"), 243: ("素", "high"),
    265: ("衝突", "high"), 266: ("衝突", "high"),
    269: ("素", "high"), 276: ("素", "high"), 278: ("素", "high"), 279: ("素", "high"),
    291: ("素", "med"), 300: ("素", "high"),
}
lines = json.loads((OUT / "S02E01.asr.json").read_text(encoding="utf-8"))
zh = {}
p = OUT / "S02E01.jsonl"
if p.exists():
    for l in p.open(encoding="utf-8"):
        r = json.loads(l)
        if r.get("zh"):
            zh[round(r["start"], 1)] = r["zh"]
rows = []
for i, (mode, conf) in sorted(TAGS.items()):
    l = lines[i]
    rows.append({"ep": "S02E01", "idx": i, "start": l["start"], "end": l["end"],
                 "ja": l["ja"], "zh": zh.get(round(l["start"], 1), ""), "mode": mode, "conf": conf})
with open(OUT / "chizuru_gold_S02E01.jsonl", "w", encoding="utf-8") as f:
    for r in rows:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")
print("S02E01 gold:", len(rows))
