"""给每行打「女性声线(千鹤候选)」标记：只算基频 F0，快（约 15 秒/集）。
输出 out\\<ep>.spk.jsonl
"""
import json, pathlib, sys, time
import numpy as np

REPO = pathlib.Path(r"E:\RentAGirl")
OUT = REPO / "out"
RAW = REPO / "raw"
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from speaker_id import f0_median, line_audio
from process_episode import decode

F0_FEMALE = 200.0


def main():
    eps = sorted(p.stem.replace(".asr", "") for p in OUT.glob("S*E*.asr.json"))
    todo = [e for e in eps if not (OUT / f"{e}.f0.jsonl").exists()]
    print(f"{len(todo)} pending", flush=True)
    for ep in todo:
        t0 = time.time()
        lines = json.loads((OUT / f"{ep}.asr.json").read_text(encoding="utf-8"))
        cut = json.loads((OUT / f"{ep}.cut.json").read_text(encoding="utf-8"))["cut_s"]
        audio = decode(RAW / f"{ep}.mp4", cut)
        recs = []
        for l in lines:
            f0 = f0_median(line_audio(audio, l))
            recs.append({**l, "f0": round(f0, 1), "female": bool(f0 >= F0_FEMALE)})
        with open(OUT / f"{ep}.f0.jsonl", "w", encoding="utf-8") as g:
            for r in recs:
                g.write(json.dumps(r, ensure_ascii=False) + "\n")
        n = sum(1 for r in recs if r["female"])
        print(f"{ep}: {n}/{len(recs)} female-voiced, {time.time()-t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
