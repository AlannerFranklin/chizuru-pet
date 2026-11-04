"""生成人工审核用的索引：每个 wav -> 日文/中文/模式/来源/相似度"""
import json
import pathlib

DS = pathlib.Path(r"E:\GPTSoVITS\dataset2")
OUT = pathlib.Path(r"E:\RentAGirl\out")
REVIEW = pathlib.Path(r"E:\RentAGirl\review")
REVIEW.mkdir(parents=True, exist_ok=True)

gold = [json.loads(l) for l in (OUT / "chizuru_gold.jsonl").open(encoding="utf-8")]

gold_key = {(r["ep"], r["idx"]): r for r in gold}

_all_lines = [l for l in (DS / "list.txt").read_text(encoding="utf-8").strip().split("\n") if l]
_sims_recs = json.loads((DS.parent / "sims.json").read_text(encoding="utf-8")) if (DS.parent / "sims.json").exists() else []
sims = {}
for _l, _r in zip(_all_lines, _sims_recs):
    sims[pathlib.Path(_l.split("|")[0]).name] = _r

auto = [json.loads(l) for l in (OUT / "chizuru_auto.jsonl").open(encoding="utf-8")]

# 自动标注：按 (ep, ja) 建索引，用于补中文
zh_by_ep_ja = {}
for ep in {a["ep"] for a in auto}:
    p = OUT / f"{ep}.jsonl"
    if not p.exists():
        continue
    m = {}
    for line in p.open(encoding="utf-8"):
        r = json.loads(line)
        if r.get("zh"):
            m[r.get("ja", "")] = r["zh"]
    zh_by_ep_ja[ep] = m

items = []
for line in (DS / "list.txt").read_text(encoding="utf-8").strip().split("\n"):
    if not line:
        continue
    parts = line.split("|")
    p = pathlib.Path(parts[0])
    text = "|".join(parts[3:]) if len(parts) > 3 else ""
    name = p.name
    ep = name.split("_")[0]
    src = "gold" if "_gold_" in name else "auto"
    zh, mode = "", "素"
    if src == "gold":
        idx = int(name.split("_gold_")[1].split(".")[0])
        r = gold_key.get((ep, idx))
        if r:
            zh, mode = r.get("zh", ""), r.get("mode") or "素"
    else:
        zh = zh_by_ep_ja.get(ep, {}).get(text, "")
        for r in auto:
            if r["ep"] == ep and r["ja"] == text:
                mode = r.get("mode") or "素"
                break
    items.append({
        "id": name,
        "file": str(p),
        "ep": ep,
        "src": src,
        "ja": text,
        "zh": zh,
        "mode": mode,
        "sim": round(sims.get(name, {}).get("sim", 0), 3),
        "dur": round(sims.get(name, {}).get("dur", 0), 2),
    })

(REVIEW / "index.json").write_text(json.dumps(items, ensure_ascii=False), encoding="utf-8")
print("items", len(items), "gold", sum(1 for i in items if i["src"] == "gold"),
      "auto", sum(1 for i in items if i["src"] == "auto"))
print("total min", round(sum(i["dur"] for i in items) / 60, 1))
