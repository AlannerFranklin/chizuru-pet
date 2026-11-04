import json, sys, pathlib

ep = sys.argv[1] if len(sys.argv) > 1 else "S01E03"
OUT = pathlib.Path(r"E:\RentAGirl\out")
rows = [json.loads(l) for l in (OUT / "chizuru_text.jsonl").open(encoding="utf-8")]
sel = [r for r in rows if r["ep"] == ep]
lines = []
for r in sel:
    lines.append("%6.1f  %s" % (r["start"], r["ja"]))
(OUT / f"{ep}_candidates.txt").write_text("\n".join(lines), encoding="utf-8")
print(f"{ep}: {len(sel)} candidates written")
