"""从「你标成好听」的片段里，按模式各挑一段最干净的当情绪参考音频。"""
import json
import pathlib

REPO = pathlib.Path(r"E:\RentAGirl")
OUT = REPO / "out"
DS6 = pathlib.Path(r"E:\GPTSoVITS\dataset6")
REVIEW = REPO / "review"
DST = pathlib.Path(r"E:\GPTSoVITS\refs\v5")
DST.mkdir(parents=True, exist_ok=True)

ok = set()
for line in (REVIEW / "votes.jsonl").open(encoding="utf-8"):
    line = line.strip()
    if not line:
        continue
    try:
        r = json.loads(line)
    except Exception:
        continue
    if r.get("vote") == "ok":
        ok.add(r["id"])

meta = {m["id"]: m for m in json.loads((DS6 / "index.json").read_text(encoding="utf-8"))}
gold = [json.loads(l) for l in (OUT / "chizuru_gold.jsonl").open(encoding="utf-8")]
gold_key = {(r["ep"], r["idx"]): r for r in gold}
auto = [json.loads(l) for l in (OUT / "chizuru_auto.jsonl").open(encoding="utf-8")]
auto_key = {(r["ep"], r["ja"]): r for r in auto}

best = {}
for cid in ok:
    m = meta.get(cid)
    if not m:
        continue
    name = cid
    ep = name.split("_")[0]
    mode = None
    if "_gold_" in name:
        idx = int(name.split("_gold_")[1].split(".")[0])
        r = gold_key.get((ep, idx))
        if r:
            mode = r.get("mode")
    else:
        r = auto_key.get((ep, m["ja"]))
        if r:
            mode = r.get("mode")
    if not mode:
        continue
    if not (3.4 <= m["dur"] <= 7.0):
        continue
    cur = best.get(mode)
    if cur is None or m["sim"] > cur["sim"]:
        best[mode] = m
        best[mode]["_mode"] = mode

refs = {}
for mode, m in best.items():
    refs[mode] = {"file": m["file"], "text": m["ja"], "dur": m["dur"], "sim": m["sim"]}
    print(f"{mode}: sim={m['sim']} {m['dur']}s {pathlib.Path(m['file']).name} | {m['ja'][:34]}")

(DST / "refs.json").write_text(json.dumps(refs, ensure_ascii=False, indent=2), encoding="utf-8")
print("saved", DST / "refs.json")
