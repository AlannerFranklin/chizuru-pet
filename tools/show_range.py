import json, sys, pathlib
OUT = pathlib.Path(r"E:\RentAGirl\out")
ep = sys.argv[1]
a, b = int(sys.argv[2]), int(sys.argv[3])
lines = json.loads((OUT / f"{ep}.asr.json").read_text(encoding="utf-8"))
zh = {}
p = OUT / f"{ep}.jsonl"
if p.exists():
    for l in p.open(encoding="utf-8"):
        r = json.loads(l)
        if r.get("zh"):
            zh[round(r["start"], 1)] = r["zh"]
for i in range(a, min(b, len(lines))):
    l = lines[i]
    z = zh.get(round(l["start"], 1), "")
    print(f"{i:03d} {l['start']:7.1f} {l['ja']}" + (f"  || {z}" if z else ""))
