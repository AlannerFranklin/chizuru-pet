"""用 UVR 生态里的 MelBand Roformer 人声模型分离，测声纹相似度与底噪。"""
import pathlib
import numpy as np
import soundfile as sf

from audio_separator.separator import Separator

OUT = pathlib.Path(r"E:\RentAGirl\out\uvr_test")
OUT.mkdir(parents=True, exist_ok=True)

sep = Separator(model_file_dir=str(OUT / "models"), output_dir=str(OUT), output_format="WAV")
sep.load_model("vocals_mel_band_roformer.ckpt")

targets = [
    r"E:\GPTSoVITS\dataset\raw\S01E08_005.wav",
    r"E:\GPTSoVITS\refs\素.wav",
]
for t in targets:
    p = pathlib.Path(t)
    if not p.exists():
        print("missing", p.name)
        continue
    out = sep.separate(str(p))
    print(p.name, "->", out, flush=True)
