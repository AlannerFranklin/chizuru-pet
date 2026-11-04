"""用 ModelScope 的 3D-Speaker diarization 管线跑一集，输出说话人时间段。
用法: python diarize_ms.py S01E07
输出: out/<ep>.diar.json  [[start,end,speaker_id], ...]
"""
import json, sys, time, pathlib
import numpy as np
import soundfile as sf

REPO = pathlib.Path(r"E:\RentAGirl")
OUT = REPO / "out"
sys.path.insert(0, str(REPO / "tools"))
from process_episode import decode

ep = sys.argv[1]
wav = OUT / f"{ep}.wav"
meta = json.loads((OUT / f"{ep}.cut.json").read_text(encoding="utf-8"))
if not wav.exists():
    audio = decode(REPO / "raw" / f"{ep}.mp4", meta["cut_s"])
    sf.write(str(wav), audio, 16000)
    print(f"wav written {len(audio)/16000:.0f}s", flush=True)

from modelscope.pipelines import pipeline
t0 = time.time()
p = pipeline(task='speaker-diarization', model='iic/speech_campplus_speaker-diarization_common')
print(f"pipeline built {time.time()-t0:.1f}s", flush=True)

t0 = time.time()
r = p(str(wav))
segs = [[float(a), float(b), int(c)] for a, b, c in r["text"]]
print(f"diarized {time.time()-t0:.1f}s, {len(segs)} segments", flush=True)

(OUT / f"{ep}.diar.json").write_text(json.dumps(segs, ensure_ascii=False), encoding="utf-8")
spk = sorted({s[2] for s in segs})
dur = {}
for a, b, c in segs:
    dur[c] = dur.get(c, 0) + (b - a)
print("speakers:", {k: round(v / 60, 1) for k, v in sorted(dur.items())}, "minutes", flush=True)
