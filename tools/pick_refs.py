"""为四种模式各挑一段参考音频（4~7 秒、金标、响度正常）。"""
import json, pathlib
import soundfile as sf
import numpy as np

DS = pathlib.Path(r"E:\GPTSoVITS\dataset3")
OUT = pathlib.Path(r"E:\RentAGirl\out")
rows = [json.loads(l) for l in (OUT / "chizuru_gold.jsonl").open(encoding="utf-8")]
lines = [l for l in (DS / "list.txt").read_text(encoding="utf-8").strip().split("\n") if l]

by_name = {}
for l in lines:
    p = pathlib.Path(l.split("|")[0])
    by_name[p.stem] = l

# 找每段对应金标（文件名格式 <ep>_gold_<idx>）
best = {}
for l in lines:
    parts = l.split("|")
    p = pathlib.Path(parts[0])
    text = parts[3] if len(parts) > 3 else ""
    if "_gold_" not in p.name:
        continue
    ep = p.name.split("_gold_")[0]
    idx = int(p.name.split("_gold_")[1].split(".")[0])
    mode = None
    for r in rows:
        if r["ep"] == ep and r["idx"] == idx:
            mode = r.get("mode")
            break
    if not mode:
        continue
    w, sr = sf.read(str(p), dtype="float32")
    dur = w.shape[0] / sr
    rms = float(np.sqrt(np.mean(w ** 2)))
    if not (3.5 <= dur <= 7.0) or rms < 0.05:
        continue
    best.setdefault(mode, []).append((dur, rms, str(p), text))

for mode, items in best.items():
    items.sort(key=lambda x: -x[0])
    print(f"== {mode} ({len(items)})")
    for dur, rms, p, t in items[:5]:
        print(f"  {dur:.1f}s rms={rms:.3f} {pathlib.Path(p).name} | {t[:30]}")
