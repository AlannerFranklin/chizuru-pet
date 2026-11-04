"""从 ASR 缓存(out\\<ep>.asr.json)汇总日文语料，不需要 OCR。
输出 out\\corpus_ja.jsonl + out\\corpus_ja_stats.json
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
    rows = []
    per_ep = {}
    for f in sorted(OUT.glob("S*E*.asr.json")):
        ep = f.stem.replace(".asr", "")
        lines = json.loads(f.read_text(encoding="utf-8"))
        for l in lines:
            rows.append({"ep": ep, "start": l["start"], "end": l["end"],
                         "ja": l["ja"], "mode_guess": guess_mode(l["ja"])})
        per_ep[ep] = {"lines": len(lines), "ja_chars": sum(len(l["ja"]) for l in lines)}

    with open(OUT / "corpus_ja.jsonl", "w", encoding="utf-8") as g:
        for r in rows:
            g.write(json.dumps(r, ensure_ascii=False) + "\n")

    modes = collections.Counter(r["mode_guess"] for r in rows)
    stats = {"episodes": len(per_ep), "lines": len(rows),
             "ja_chars": sum(len(r["ja"]) for r in rows),
             "mode_guess": dict(modes), "per_episode": per_ep}
    (OUT / "corpus_ja_stats.json").write_text(json.dumps(stats, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: v for k, v in stats.items() if k != "per_episode"}, ensure_ascii=False))
    tot = stats["lines"]
    print(f"平均每集 {tot/len(per_ep):.0f} 行, 平均每行 {stats['ja_chars']/tot:.1f} 字")


if __name__ == "__main__":
    main()
