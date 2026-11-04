import json, pathlib

OUT = pathlib.Path(r"E:\RentAGirl\out")

TAGS = {
    26: ("素", "med"),
    61: ("素", "high"),
    134: ("素", "high"), 135: ("素", "high"), 136: ("素", "high"), 137: ("素", "high"),
    138: ("素", "high"), 144: ("素", "high"), 145: ("素", "high"), 147: ("素", "high"),
    148: ("素", "high"), 149: ("素", "high"), 153: ("素", "high"), 154: ("素", "high"),
    155: ("素", "high"), 156: ("素", "high"), 157: ("素", "high"), 158: ("素", "high"),
    160: ("素", "med"), 162: ("素", "high"), 166: ("素", "high"), 167: ("素", "med"),
    168: ("素", "high"), 169: ("素", "high"), 170: ("素", "high"),
    200: ("素", "high"), 229: ("素", "med"), 253: ("営業", "high"),
    266: ("素", "high"), 268: ("素", "high"), 269: ("素", "high"), 271: ("素", "high"),
    272: ("素", "high"), 274: ("素", "high"), 275: ("素", "high"), 276: ("素", "high"),
    278: ("素", "high"), 280: ("素", "high"), 281: ("素", "high"), 282: ("素", "high"),
    285: ("素", "high"), 286: ("衝突", "high"), 287: ("衝突", "high"),
    288: ("衝突", "high"), 289: ("衝突", "high"), 290: ("衝突", "high"),
    292: ("素", "high"),
    305: ("素", "med"), 313: ("素", "high"), 314: ("素", "high"), 315: ("素", "high"),
    321: ("素", "med"), 322: ("素", "high"), 324: ("素", "high"), 325: ("素", "med"),
    326: ("素", "high"), 327: ("素", "med"), 328: ("素", "med"), 329: ("素", "high"),
}

lines = json.loads((OUT / "S01E04.asr.json").read_text(encoding="utf-8"))
zh = {}
p = OUT / "S01E04.jsonl"
if p.exists():
    for l in p.open(encoding="utf-8"):
        r = json.loads(l)
        if r.get("zh"):
            zh[round(r["start"], 1)] = r["zh"]

rows = []
for i, (mode, conf) in sorted(TAGS.items()):
    l = lines[i]
    ja = l.get("ja") or l.get("text", "")
    rows.append({"ep": "S01E04", "idx": i, "start": l["start"], "end": l["end"],
                 "ja": ja, "zh": zh.get(round(l["start"], 1), ""), "mode": mode, "conf": conf})

with open(OUT / "chizuru_gold_S01E04.jsonl", "w", encoding="utf-8") as f:
    for r in rows:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")
print("S01E04 gold:", len(rows))
