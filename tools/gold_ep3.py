import json, pathlib

OUT = pathlib.Path(r"E:\RentAGirl\out")

# 人工通读 S01E03 转写后标出的千鹤台词（index -> mode, conf）
TAGS = {
    74: ("素", "high"), 76: ("素", "high"), 77: ("素", "high"), 78: ("素", "high"),
    79: ("素", "high"), 80: ("素", "high"), 88: ("素", "high"), 89: ("素", "high"),
    90: ("素", "med"), 93: ("素", "high"), 94: ("素", "high"), 95: ("素", "high"),
    136: ("素", "med"), 187: ("営業", "med"), 192: ("営業", "high"), 196: ("営業", "high"),
    200: ("素", "med"), 207: ("素", "high"), 208: ("素", "high"), 209: ("素", "high"),
    211: ("素", "high"), 212: ("素", "high"), 232: ("素", "high"), 236: ("素", "high"),
    237: ("素", "high"), 238: ("素", "high"), 239: ("素", "high"), 247: ("素", "high"),
    255: ("衝突", "high"), 256: ("衝突", "high"), 257: ("衝突", "high"),
    258: ("衝突", "high"), 259: ("衝突", "high"), 260: ("衝突", "high"),
    261: ("衝突", "high"), 279: ("営業", "high"), 280: ("営業", "high"),
    284: ("営業", "high"), 286: ("営業", "high"), 287: ("営業", "high"),
    307: ("営業", "high"), 313: ("素", "high"), 314: ("素", "high"),
    316: ("素", "med"), 318: ("素", "med"), 319: ("素", "high"), 320: ("素", "high"),
    352: ("衝突", "high"), 357: ("素", "high"),
}

lines = json.loads((OUT / "S01E03.asr.json").read_text(encoding="utf-8"))
zh = {}
p = OUT / "S01E03.jsonl"
if p.exists():
    for l in p.open(encoding="utf-8"):
        r = json.loads(l)
        if r.get("zh"):
            zh[round(r["start"], 1)] = r["zh"]

rows = []
for i, (mode, conf) in sorted(TAGS.items()):
    l = lines[i]
    rows.append({"ep": "S01E03", "idx": i, "start": l["start"], "end": l["end"],
                 "ja": l["ja"] if "ja" in l else l.get("text", ""),
                 "zh": zh.get(round(l["start"], 1), ""), "mode": mode, "conf": conf})

# asr.json 的键是 ja
for r in rows:
    if not r["ja"]:
        r["ja"] = lines[r["idx"]].get("ja") or lines[r["idx"]].get("text", "")

with open(OUT / "chizuru_gold_S01E03.jsonl", "w", encoding="utf-8") as f:
    for r in rows:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")
print("S01E03 gold:", len(rows))
