import json, pathlib

OUT = pathlib.Path(r"E:\RentAGirl\out")

TAGS = {
    5: ("素", "high"), 6: ("素", "med"), 7: ("素", "high"), 8: ("素", "high"),
    10: ("素", "high"),
    35: ("素", "high"), 42: ("素", "med"),
    88: ("素", "high"), 103: ("素", "high"), 106: ("素", "high"), 108: ("素", "high"),
    148: ("営業", "high"), 149: ("営業", "high"), 155: ("素", "high"),
    181: ("衝突", "high"), 186: ("衝突", "med"), 187: ("衝突", "high"),
    188: ("衝突", "high"), 189: ("衝突", "high"), 191: ("素", "high"),
    192: ("素", "high"), 193: ("素", "high"), 196: ("素", "med"),
    202: ("素", "high"), 209: ("素", "high"), 210: ("素", "high"),
    216: ("素", "high"), 220: ("素", "high"), 221: ("素", "high"),
    222: ("素", "high"), 224: ("素", "high"), 226: ("素", "med"),
    228: ("素", "high"), 232: ("素", "med"), 233: ("素", "high"),
    235: ("素", "high"), 237: ("素", "high"), 238: ("素", "high"),
    251: ("営業", "high"), 253: ("営業", "med"), 257: ("素", "med"),
    262: ("営業", "med"), 266: ("素", "med"), 274: ("素", "med"),
    282: ("素", "med"), 284: ("素", "med"),
    291: ("素", "high"), 292: ("素", "high"), 296: ("素", "high"),
}

lines = json.loads((OUT / "S01E05.asr.json").read_text(encoding="utf-8"))
zh = {}
p = OUT / "S01E05.jsonl"
if p.exists():
    for l in p.open(encoding="utf-8"):
        r = json.loads(l)
        if r.get("zh"):
            zh[round(r["start"], 1)] = r["zh"]

rows = []
for i, (mode, conf) in sorted(TAGS.items()):
    l = lines[i]
    ja = l.get("ja") or l.get("text", "")
    rows.append({"ep": "S01E05", "idx": i, "start": l["start"], "end": l["end"],
                 "ja": ja, "zh": zh.get(round(l["start"], 1), ""), "mode": mode, "conf": conf})

with open(OUT / "chizuru_gold_S01E05.jsonl", "w", encoding="utf-8") as f:
    for r in rows:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")

all_rows = []
for f in sorted(OUT.glob("chizuru_gold_*.jsonl")):
    all_rows += [json.loads(l) for l in f.open(encoding="utf-8")]
with open(OUT / "chizuru_gold.jsonl", "w", encoding="utf-8") as f:
    for r in all_rows:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")
print("S01E05 gold:", len(rows), "| total gold:", len(all_rows))
