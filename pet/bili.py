"""桌宠调用 B 站：跑一次「逛一会儿」，把她的感受带回来。"""
import json
import os
import pathlib
import random
import re
import subprocess

ROOT = pathlib.Path(r"E:\RentAGirl")
PY = r"E:\test\uv-venv\Scripts\pythonw.exe"
SCRIPT = str(ROOT / "tools" / "bili_session.py")
LOG = ROOT / "out" / "bili_log.jsonl"
CREATE_NO_WINDOW = 0x08000000

ZONES = ["动画", "音乐", "舞蹈", "生活", "知识", "影视"]


def run(post=False, rounds=3, zone=""):
    """跑一次浏览，返回 {'keyword','watched','ja','zh'} 或 None。"""
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    cmd = [PY, "-u", SCRIPT, "--rounds", str(rounds)]
    if post:
        cmd.append("--post")
    if zone:
        cmd += ["--zone", zone]
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                           timeout=300, env=env, creationflags=CREATE_NO_WINDOW)
    except Exception as e:
        print("bili run failed:", e)
        return None
    out = p.stdout or ""
    ja = zh = kw = ""
    watched = []
    for line in out.splitlines():
        if line.startswith("她想搜："):
            kw = line.split("她想搜：", 1)[1].split("（")[0].strip()
        elif re.match(r"^\[\d+\] ", line):
            watched.append(line.split("] ", 1)[1].strip())
        elif line.startswith("SUMMARY_JA:"):
            ja = line.split("SUMMARY_JA:", 1)[1].strip()
        elif line.startswith("SUMMARY_ZH:"):
            zh = line.split("SUMMARY_ZH:", 1)[1].strip()
    if not ja:
        print(out[-400:])
        return None
    return {"keyword": kw, "watched": watched, "ja": ja, "zh": zh}


if __name__ == "__main__":
    print(json.dumps(run(rounds=3), ensure_ascii=False))
