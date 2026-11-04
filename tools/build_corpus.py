"""汇总 out\\*.jsonl -> out\\corpus.jsonl，并出统计。
用法: python build_corpus.py
"""
import json, pathlib, re, collections

REPO = pathlib.Path(r"E:\RentAGirl")
OUT = REPO / "out"

KEIGO = re.compile(r"(です|ます|ございます|お客様|よろしく|ありがとうございます|申し訳)")
CONFLICT = re.compile(r"(バカ|ばか|通報|事務所|契約|そんなわけ|ふざけ|脱線|営業妨害|天地が)")
SOFT = re.compile(r"(ばあちゃん|おばあちゃん|寂し|夢|芝居|舞台|オーディション)")


def guess_mode(ja):
    if CONFLICT.search(ja):
        return "衝突"
    if SOFT.search(ja):
        return "软肋"
    if KEIGO.search(ja):
        return "営業"
    return "素"


def main():
    import re
    files = [p for p in sorted(OUT.glob("S*.jsonl")) if re.fullmatch(r"S\d\dE\d\d\.jsonl", p.name)]
    rows = []
    per_ep = {}
    for f in files:
        ep = f.stem
        n = 0
        with_zh = 0
        for line in f.open(encoding="utf-8"):
            r = json.loads(line)
            r["ep"] = ep
            r["mode_guess"] = guess_mode(r["ja"])
            ja_len = len(r["ja"])
            zh_len = len(r.get("zh") or "")
            # 对齐可信度：中日字数比通常在 0.35~1.2；超出范围多半是「取错行」
            ratio = (zh_len / ja_len) if ja_len else 0
            r["align_ok"] = bool(zh_len) and (0.3 <= ratio <= 1.4) and ja_len >= 3
            rows.append(r)
            n += 1
            with_zh += 1 if r.get("zh") else 0
        per_ep[ep] = {"lines": n, "with_zh": with_zh,
                      "zh_rate": round(with_zh / n, 3) if n else 0}
        print(f"{ep}: {n} lines, zh {with_zh}")

    with open(OUT / "corpus.jsonl", "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    modes = collections.Counter(r["mode_guess"] for r in rows)
    stats = {
        "episodes": len(files),
        "lines": len(rows),
        "ja_chars": sum(len(r["ja"]) for r in rows),
        "with_zh": sum(1 for r in rows if r.get("zh")),
        "mode_guess": dict(modes),
        "per_episode": per_ep,
    }
    (OUT / "corpus_stats.json").write_text(json.dumps(stats, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: v for k, v in stats.items() if k != "per_episode"}, ensure_ascii=False))


if __name__ == "__main__":
    main()
