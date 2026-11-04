import json, pathlib
import numpy as np

REPO = pathlib.Path(r"E:\RentAGirl")
OUT = REPO / "out"
SR = 16000


def f0_median(a, fmin=70, fmax=400):
    a = np.asarray(a, dtype=np.float64)
    a = a - a.mean()
    if a.size < SR * 0.3 or np.abs(a).max() < 1e-4:
        return 0.0
    frame, hop = int(0.04 * SR), int(0.02 * SR)
    lmin, lmax = int(SR / fmax), int(SR / fmin)
    vals = []
    for st in range(0, a.size - frame, hop):
        x = a[st:st + frame]
        if np.sqrt((x ** 2).mean()) < 0.01:
            continue
        x = x * np.hamming(frame)
        ac = np.correlate(x, x, mode="full")[frame - 1:]
        if ac[0] <= 0:
            continue
        ac = ac / ac[0]
        seg = ac[lmin:lmax]
        if seg.size == 0:
            continue
        peak = seg.max()
        if peak < 0.3:
            continue
        # 取「第一个超过 0.85*峰值」的局部极大，避免倍频误判
        cand = np.where((seg[1:-1] > seg[:-2]) & (seg[1:-1] >= seg[2:]) & (seg[1:-1] > 0.85 * peak))[0] + 1
        if cand.size == 0:
            continue
        lag = cand[0] + lmin
        vals.append(SR / lag)
    return float(np.median(vals)) if vals else 0.0


if __name__ == "__main__":
    from process_episode import decode
    audio = decode(REPO / "raw" / "S01E01.mp4", 1468.5)
    for name, (a, b) in {"kazuya_3_15": (3, 15), "chizuru_474_510": (474, 510),
                         "kazuya_1100_1140": (1100, 1140), "chizuru_1150_1200": (1150, 1200)}.items():
        w = audio[int(a * SR):int(b * SR)]
        print(name, round(f0_median(w), 1), "Hz")
