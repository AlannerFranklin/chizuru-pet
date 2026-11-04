"""按声纹相似度阈值挑选片段，复制到新数据集目录并生成 list.txt。
用法: python select_clips.py 0.60
"""
import json, pathlib, shutil, sys
import soundfile as sf

DS2 = pathlib.Path(r"E:\GPTSoVITS\dataset2")
DS3 = pathlib.Path(r"E:\GPTSoVITS\dataset3")
TH = float(sys.argv[1]) if len(sys.argv) > 1 else 0.60

sims = json.loads((DS2.parent / "sims.json").read_text(encoding="utf-8"))
lines = [l for l in (DS2 / "list.txt").read_text(encoding="utf-8").strip().split("\n") if l]
assert len(sims) == len(lines), (len(sims), len(lines))

raw = DS3 / "raw"
raw.mkdir(parents=True, exist_ok=True)
kept = 0
total = 0.0
with (DS3 / "list.txt").open("w", encoding="utf-8") as f:
    for rec, line in zip(sims, lines):
        if rec["sim"] < TH:
            continue
        parts = line.split("|")
        src = pathlib.Path(parts[0])
        dst = raw / src.name
        if not dst.exists():
            shutil.copy2(src, dst)
        f.write(f"{dst}|" + "|".join(parts[1:]) + "\n")
        kept += 1
        total += rec["dur"]
print(f"kept {kept} clips, {total/60:.1f} min at th>={TH}")
