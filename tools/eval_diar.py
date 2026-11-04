"""用 diarization 结果 + 金标，评估「自动标千鹤」的精确率/召回率。
用法: python eval_diar.py S01E07 [suffix]   suffix 默认 diar，可传 pydiar
"""
import json, pathlib, sys, collections

OUT = pathlib.Path(r"E:\RentAGirl\out")


def gold_for(ep):
    rows = [json.loads(l) for l in (OUT / "chizuru_gold.jsonl").open(encoding="utf-8")]
    return [r for r in rows if r["ep"] == ep]


def ov(a, b, c, d):
    return max(0.0, min(b, d) - max(a, c))


def evaluate(ep, suffix="diar"):
    diar = json.loads((OUT / f"{ep}.{suffix}.json").read_text(encoding="utf-8"))
    lines = json.loads((OUT / f"{ep}.asr.json").read_text(encoding="utf-8"))
    gold_ts = [g["start"] for g in gold_for(ep)]

    line_spk = []
    for l in lines:
        best, bov = None, 0.0
        for a, b, c in diar:
            o = ov(l["start"], l["end"], a, b)
            if o > bov:
                best, bov = c, o
        line_spk.append(best)

    is_gold = [any(abs(l["start"] - t) <= 0.6 for t in gold_ts) for l in lines]
    cnt = collections.Counter(s for s, g in zip(line_spk, is_gold) if g)
    mine = cnt.most_common(1)[0][0] if cnt else None

    tp = sum(1 for s, g in zip(line_spk, is_gold) if g and s == mine)
    fn = sum(1 for s, g in zip(line_spk, is_gold) if g and s != mine)
    fp = sum(1 for s, g in zip(line_spk, is_gold) if (not g) and s == mine)
    tn = sum(1 for s, g in zip(line_spk, is_gold) if (not g) and s != mine)
    prec = tp / (tp + fp) if tp + fp else 0
    rec = tp / (tp + fn) if tp + fn else 0
    f1 = 2 * prec * rec / (prec + rec) if prec + rec else 0
    print(f"{ep} [{suffix}]: id={mine} P={prec:.2f} R={rec:.2f} F1={f1:.2f} "
          f"(tp={tp} fp={fp} fn={fn} tn={tn})")
    print("   gold per speaker:", dict(cnt))


if __name__ == "__main__":
    ep = sys.argv[1] if len(sys.argv) > 1 else "S01E07"
    suf = sys.argv[2] if len(sys.argv) > 2 else "diar"
    evaluate(ep, suf)
