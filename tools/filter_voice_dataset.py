"""用千鹤的声纹均值筛掉训练集里的杂音/别人说话。
用法: python filter_voice_dataset.py
读 list.txt，输出 list_filtered.txt，并把不合格的 wav 移到 rejects/
"""
import pathlib

import numpy as np
import soundfile as sf
import torch

REPO = pathlib.Path(r"E:\RentAGirl")
DS = pathlib.Path(r"E:\GPTSoVITS\dataset")
BASE = pathlib.Path(r"E:\test\pyannote")
C = np.load(REPO / "out" / "chizuru_enroll.npy")
EMB = None
SR = 16000


def embed(wav):
    global EMB
    if EMB is None:
        from pyannote.audio import Model
        EMB = Model.from_pretrained(str(BASE / "emb"))
    if wav.size < int(0.5 * SR):
        wav = np.pad(wav, (0, int(0.5 * SR) - wav.size))
    w = torch.from_numpy(wav.astype(np.float32)).unsqueeze(0).unsqueeze(0)
    with torch.no_grad():
        e = EMB(w).squeeze().cpu().numpy()
    return e / (np.linalg.norm(e) + 1e-9)


def main():
    lines = (DS / "list.txt").read_text(encoding="utf-8").strip().split("\n")
    keep, drop = [], []
    for line in lines:
        parts = line.split("|")
        if len(parts) < 4:
            continue
        path, spk, lang, text = parts[0], parts[1], parts[2], "|".join(parts[3:])
        wav, sr = sf.read(path, dtype="float32")
        if wav.ndim > 1:
            wav = wav.mean(axis=1)
        if sr != SR:
            n = int(wav.size * SR / sr)
            wav = np.interp(np.linspace(0, wav.size - 1, n), np.arange(wav.size), wav).astype(np.float32)
        sim = float(embed(wav) @ C)
        (keep if sim >= 0.5 else drop).append((line, sim))

    rej = DS / "rejects"
    rej.mkdir(exist_ok=True)
    for line, sim in drop:
        p = pathlib.Path(line.split("|")[0])
        if p.exists():
            p.replace(rej / p.name)

    with (DS / "list_filtered.txt").open("w", encoding="utf-8") as f:
        for line, sim in keep:
            f.write(line + "\n")
    print(f"keep {len(keep)} / {len(lines)}  (drop {len(drop)})")
    for line, sim in keep[:5]:
        print(round(sim, 3), pathlib.Path(line.split('|')[0]).name)
    for line, sim in drop[:5]:
        print("DROP", round(sim, 3), pathlib.Path(line.split('|')[0]).name)


if __name__ == "__main__":
    main()
