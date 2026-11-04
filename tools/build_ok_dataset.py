"""按人工审核结果构建「纯好」训练集：只保留 vote=ok 的片段。"""
import json
import pathlib
import shutil

DS6 = pathlib.Path(r"E:\GPTSoVITS\dataset6")
DS7 = pathlib.Path(r"E:\GPTSoVITS\dataset7")
REVIEW = pathlib.Path(r"E:\RentAGirl\review")

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

raw = DS7 / "raw"
raw.mkdir(parents=True, exist_ok=True)
count = 0
total = 0.0
with (DS7 / "list.txt").open("w", encoding="utf-8") as f:
    for line in (DS6 / "list.txt").read_text(encoding="utf-8").strip().split("\n"):
        if not line:
            continue
        src = pathlib.Path(line.split("|")[0])
        if src.name not in ok:
            continue
        dst = raw / src.name
        if not dst.exists():
            try:
                dst.hardlink_to(src)
            except OSError:
                shutil.copy2(src, dst)
        f.write(f"{dst}|" + "|".join(line.split("|")[1:]) + "\n")
        count += 1

print("ok clips", count)
