import json, sys, pathlib

ep = sys.argv[1]
OUT = pathlib.Path(r"E:\RentAGirl\out")
lines = json.loads((OUT / f"{ep}.asr.json").read_text(encoding="utf-8"))
zh = {}
p = OUT / f"{ep}.jsonl"
if p.exists():
    for l in p.open(encoding="utf-8"):
        r = json.loads(l)
        if r.get("zh"):
            zh[round(r["start"], 1)] = r["zh"]

out = []
for i, l in enumerate(lines):
    z = zh.get(round(l["start"], 1), "")
    out.append("%03d %6.1f %s%s" % (i, l["start"], l["ja"], ("  || " + z) if z else ""))
(OUT / f"{ep}_transcript.txt").write_text("\n".join(out), encoding="utf-8")
print(ep, len(lines), "lines")
