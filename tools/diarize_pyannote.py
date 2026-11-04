"""用 ModelScope 镜像的 pyannote 3.1 权重本地跑 diarization。
用法: python diarize_pyannote.py S01E07
输出: out/<ep>.pydiar.json  [[start,end,spk], ...]
"""
import json, sys, time, pathlib
import numpy as np
import soundfile as sf

REPO = pathlib.Path(r"E:\RentAGirl")
OUT = REPO / "out"
BASE = pathlib.Path(r"E:\test\pyannote")
sys.path.insert(0, str(REPO / "tools"))
from process_episode import decode

from pyannote.audio import Model, Pipeline
from pyannote.audio.core.plda import PLDA
from pyannote.audio.pipelines import SpeakerDiarization

PLDA_DIR = BASE / "plda"

ep = sys.argv[1]
wav = OUT / f"{ep}.wav"
if not wav.exists():
    meta = json.loads((OUT / f"{ep}.cut.json").read_text(encoding="utf-8"))
    audio = decode(REPO / "raw" / f"{ep}.mp4", meta["cut_s"])
    sf.write(str(wav), audio, 16000)
    print("wav written", flush=True)

t0 = time.time()
seg = Model.from_pretrained(str(BASE / "seg"))
emb = Model.from_pretrained(str(BASE / "emb"))
print(f"models loaded {time.time()-t0:.1f}s", flush=True)

plda = PLDA(transform_npz=PLDA_DIR / "xvec_transform.npz",
            plda_npz=PLDA_DIR / "plda.npz")
print("plda loaded", flush=True)

mode = sys.argv[2] if len(sys.argv) > 2 else "vbx"
kwargs = dict(
    segmentation=seg,
    embedding=emb,
    plda=plda,
    embedding_batch_size=8,
    segmentation_batch_size=8,
    embedding_exclude_overlap=True,
)
if mode == "agg":
    kwargs["clustering"] = "AgglomerativeClustering"

pipeline = SpeakerDiarization(**kwargs)
if mode == "agg":
    pipeline.instantiate({
        "clustering": {"method": "centroid", "min_cluster_size": 12, "threshold": 0.7045654963945799},
        "segmentation": {"min_duration_off": 0.0},
    })
print("mode", mode, flush=True)

t0 = time.time()
data, sr = sf.read(str(wav), dtype="float32")
import torch
waveform = torch.from_numpy(data).unsqueeze(0)
ann = pipeline({"waveform": waveform, "sample_rate": sr})
if hasattr(ann, "speaker_diarization"):
    ann = ann.speaker_diarization
segs = [[round(s.start, 2), round(s.end, 2), lab] for s, _, lab in ann.itertracks(yield_label=True)]
print(f"diarized {time.time()-t0:.1f}s, {len(segs)} segments", flush=True)

(OUT / f"{ep}.pydiar.json").write_text(json.dumps(segs, ensure_ascii=False), encoding="utf-8")
dur = {}
for a, b, c in segs:
    dur[c] = dur.get(c, 0) + (b - a)
print("speakers:", {k: round(v / 60, 1) for k, v in sorted(dur.items())}, "minutes", flush=True)
