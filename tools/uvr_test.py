"""用 UVR5 的 HP5_only_main_vocal 模型分离人声，和 demucs 结果、原始音频对比。"""
import pathlib
import numpy as np
import soundfile as sf

from audio_separator.separator import Separator

MODELS = r"D:\AIdub\RVC1006Nvidia\RVC1006Nvidia\assets\uvr5_weights"
OUT = pathlib.Path(r"E:\RentAGirl\out\uvr_test")
OUT.mkdir(parents=True, exist_ok=True)

sep = Separator(model_file_dir=MODELS, output_dir=str(OUT), output_format="WAV")
sep.load_model("HP5_only_main_vocal.pth")

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
    print(p.name, "->", out)
