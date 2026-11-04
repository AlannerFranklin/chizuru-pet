"""用 sim + 1-NN 双阈值挑「干净集」。
用法: python select_clean.py 0.65
"""
import json, pathlib, shutil, sys

DS2 = pathlib.Path(r"E:\GPTSoVITS\dataset2")
DS4 = pathlib.Path(r"E:\GPTSoVITS\dataset4")
TH = float(sys.argv[1]) if len(sys.argv) > 1 else 0.65

meta = json.loads((DS2.parent / "clean_meta.json").read_text(encoding="utf-8"))
lines = {pathlib.Path(l.split("|")[0]).name: l for l in (DS2 / "list.txt").read_text(encoding="utf-8").strip().split("\n") if l}

raw = DS4 / "raw"
raw.mkdir(parents=True, exist_ok=True)
kept = 0
total = 0.0
with (DS4 / "list.txt").open("w", encoding="utf-8") as f:
    for m in meta:
        if m["src"] == "auto" and not (m["sim"] >= TH and m["nn"] >= TH):
            continue
        name = pathlib.Path(m["path"]).name
        src = DS2 / "raw" / name
        dst = raw / name
        if not dst.exists():
            shutil.copy2(src, dst)
        parts = lines[name].split("|")
        f.write(f"{dst}|" + "|".join(parts[1:]) + "\n")
        kept += 1
        total += m["dur"]
print(f"kept {kept} clips / {total/60:.1f} min (gold all + auto sim>={TH} & 1NN>={TH})")
