import json, pathlib, collections

OUT = pathlib.Path(r"E:\RentAGirl\out")
gold = [json.loads(l) for l in (OUT / "chizuru_gold.jsonl").open(encoding="utf-8")]
auto = [json.loads(l) for l in (OUT / "chizuru_auto.jsonl").open(encoding="utf-8")]

for r in gold:
    r["conf"] = r.get("conf", "high")
allrows = gold + auto
with open(OUT / "chizuru_all.jsonl", "w", encoding="utf-8") as f:
    for r in allrows:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")

def dist(rows):
    return dict(collections.Counter(r["mode"] for r in rows))

print("gold:", len(gold), "eps:", len({r['ep'] for r in gold}), dist(gold))
print("auto:", len(auto), "eps:", len({r['ep'] for r in auto}), dist(auto))
print("total:", len(allrows), "eps:", len({r['ep'] for r in allrows}), dist(allrows))
per = collections.Counter(r["ep"] for r in allrows)
print("episodes covered:", len(per), "min/max per ep:", min(per.values()), max(per.values()))
