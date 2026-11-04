"""把所有剧集跑一遍说话人分离（pyannote VBx），已有结果的跳过。"""
import json
import pathlib
import subprocess
import sys

REPO = pathlib.Path(r"E:\RentAGirl")
OUT = REPO / "out"
PY = r"E:\test\uv-venv\Scripts\python.exe"

eps = sorted(p.stem.replace(".asr", "") for p in OUT.glob("S*.asr.json"))
todo = [e for e in eps if not (OUT / f"{e}.pydiar.json").exists()]
print("total", len(eps), "todo", len(todo), flush=True)
for ep in todo:
    print("=== ", ep, flush=True)
    r = subprocess.run([PY, "-u", str(REPO / "tools" / "diarize_pyannote.py"), ep, "vbx"])
    if r.returncode != 0:
        print("failed", ep, flush=True)
print("ALL DONE", flush=True)
