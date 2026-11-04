import json, pathlib

OUT = pathlib.Path(r"E:\RentAGirl\out")

TAGS = {
    6: ("営業", "high"), 7: ("営業", "high"), 8: ("営業", "high"), 9: ("営業", "high"),
    10: ("営業", "high"), 13: ("営業", "high"), 15: ("営業", "high"),
    63: ("衝突", "high"), 67: ("素", "high"), 70: ("素", "high"), 71: ("素", "high"),
    74: ("素", "med"), 76: ("素", "high"), 80: ("素", "high"), 81: ("素", "high"),
    82: ("素", "high"), 83: ("素", "high"), 84: ("素", "high"),
    118: ("素", "med"), 119: ("素", "med"), 121: ("素", "med"),
    152: ("衝突", "high"),
    179: ("衝突", "high"), 181: ("衝突", "high"), 182: ("衝突", "high"),
    184: ("衝突", "high"), 185: ("衝突", "high"), 186: ("衝突", "high"),
    187: ("衝突", "high"), 191: ("衝突", "high"), 196: ("衝突", "high"),
    205: ("素", "high"), 215: ("衝突", "high"), 218: ("素", "high"),
    219: ("営業", "high"), 222: ("素", "high"), 224: ("素", "med"),
    227: ("素", "high"), 228: ("素", "high"), 231: ("素", "high"),
    237: ("素", "high"), 239: ("素", "high"), 240: ("素", "high"),
    243: ("素", "high"), 245: ("素", "high"), 246: ("衝突", "high"),
    247: ("衝突", "high"), 248: ("素", "high"), 249: ("素", "high"),
    250: ("素", "high"), 251: ("素", "high"), 252: ("素", "high"),
    253: ("素", "high"), 254: ("素", "med"), 256: ("素", "high"),
    258: ("素", "high"), 260: ("素", "med"), 264: ("素", "med"),
    266: ("素", "high"), 270: ("素", "high"),
    309: ("素", "high"), 310: ("素", "high"), 311: ("素", "high"),
    312: ("素", "high"), 313: ("素", "med"), 314: ("素", "high"),
    315: ("素", "high"), 316: ("素", "high"), 317: ("素", "high"),
    318: ("素", "high"), 325: ("素", "high"), 329: ("衝突", "high"),
}

lines = json.loads((OUT / "S01E07.asr.json").read_text(encoding="utf-8"))
zh = {}
p = OUT / "S01E07.jsonl"
if p.exists():
    for l in p.open(encoding="utf-8"):
        r = json.loads(l)
        if r.get("zh"):
            zh[round(r["start"], 1)] = r["zh"]

rows = []
for i, (mode, conf) in sorted(TAGS.items()):
    l = lines[i]
    ja = l.get("ja") or l.get("text", "")
    rows.append({"ep": "S01E07", "idx": i, "start": l["start"], "end": l["end"],
                 "ja": ja, "zh": zh.get(round(l["start"], 1), ""), "mode": mode, "conf": conf})

with open(OUT / "chizuru_gold_S01E07.jsonl", "w", encoding="utf-8") as f:
    for r in rows:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")
print("S01E07 gold:", len(rows))
