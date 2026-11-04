"""自动标注规则在已有金标的 15 集上评估，选一个「精确率 >= 0.9」的阈值。
规则：score >= T 且不含明显的他人语体标记
"""
import json, pathlib, re
import numpy as np

OUT = pathlib.Path(r"E:\RentAGirl\out")
EPS = ["S01E01", "S01E02", "S01E03", "S01E04", "S01E05", "S01E06", "S01E07",
       "S01E08", "S01E09", "S01E10", "S01E11", "S01E12", "S02E01", "S02E02", "S02E03"]
BAD = re.compile(r"(カズヤさん|俺|おれ|僕|ぼく|だぜ|かよ|てめえ|ふざけんな|あたし)")


def load(ep):
    lines = json.loads((OUT / f"{ep}.asr.json").read_text(encoding="utf-8"))
    E = np.load(OUT / f"{ep}.lineemb.npy")
    C = np.load(OUT / "enroll_all.npy")
    sims = E @ C
    rows = [json.loads(l) for l in (OUT / "chizuru_gold.jsonl").open(encoding="utf-8")]
    gold = {round(r["start"], 1) for r in rows if r["ep"] == ep}
    y = np.array([1 if round(l["start"], 1) in gold else 0 for l in lines])
    return lines, sims, y


def main():
    data = {ep: load(ep) for ep in EPS}
    print(f"{'th':>5}  {'P':>5} {'R':>5}  {'keep':>5}")
    for th in (0.50, 0.55, 0.58, 0.60, 0.62, 0.65, 0.68):
        tp = fp = fn = keep = 0
        for ep in EPS:
            lines, sims, y = data[ep]
            for i, l in enumerate(lines):
                if sims[i] >= th and not BAD.search(l["ja"]):
                    keep += 1
                    if y[i]:
                        tp += 1
                    else:
                        fp += 1
                elif y[i]:
                    fn += 1
        p = tp / keep if keep else 0
        r = tp / (tp + fn) if tp + fn else 0
        print(f"{th:5.2f}  {p:5.2f} {r:5.2f}  {keep:5d}")


if __name__ == "__main__":
    main()
