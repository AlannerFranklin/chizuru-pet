import json, pathlib

OUT = pathlib.Path(r"E:\RentAGirl\out")
rows = []
for f in sorted(OUT.glob("S*E*.asr.json")):
    ep = f.stem.replace(".asr", "")
    lines = json.loads(f.read_text(encoding="utf-8"))
    cut = json.loads((OUT / f"{ep}.cut.json").read_text(encoding="utf-8"))["cut_s"]
    last = lines[-1]["end"] if lines else 0
    rows.append((ep, cut, last, cut - last, len(lines)))

rows.sort(key=lambda r: -r[3])
print(f"{'ep':8s} {'cut':>7s} {'last_speech':>11s} {'gap':>6s} {'lines':>5s}")
for ep, cut, last, gap, n in rows[:10]:
    print(f"{ep:8s} {cut:7.1f} {last:11.1f} {gap:6.1f} {n:5d}")
print("...")
for ep, cut, last, gap, n in rows[-5:]:
    print(f"{ep:8s} {cut:7.1f} {last:11.1f} {gap:6.1f} {n:5d}")

gaps = [r[3] for r in rows]
import statistics
print(f"\ngap median={statistics.median(gaps):.1f}s  max={max(gaps):.1f}s  "
      f"episodes with gap>30s: {sum(1 for g in gaps if g > 30)}")
