"""文本侧判断「这句是不是千鹤」：日语的男女语体差异比短窗声纹可靠得多。
输出 out\\chizuru_text.jsonl（tier A/B），并在第 1 集人工标注上评估。
"""
import json, pathlib, re, collections

REPO = pathlib.Path(r"E:\RentAGirl")
OUT = REPO / "out"

MALE = [r"俺", r"おれ", r"僕", r"ぼく", r"だぜ", r"かよ", r"んだよ", r"じゃねえ",
        r"すんのか", r"やめろ", r"だろ", r"なんだよ", r"お前", r"てめえ", r"ふざけんな",
        r"してんじゃねえ", r"いけねえ", r"わるいか", r"のかよ", r"だっての", r"〜"]
FEMALE = [r"わよ", r"のよ", r"じゃん", r"でしょ", r"かしら", r"わね", r"なのよ",
          r"あたし", r"だわ", r"のよね", r"わよね", r"ですわ", r"ますわ", r"のよ?"]
POLITE = [r"です", r"ます", r"ございます"]
CHIZURU = [r"お客様", r"ご指名", r"満足度", r"指名料", r"レンタル", r"料金", r"事務所", r"契約"]

MALE_RE = re.compile("|".join(MALE))
FEMALE_RE = re.compile("|".join(FEMALE))
POLITE_RE = re.compile("|".join(POLITE))
CHIZURU_RE = re.compile("|".join(CHIZURU))


def score(ja):
    male = len(MALE_RE.findall(ja))
    female = len(FEMALE_RE.findall(ja))
    polite = len(POLITE_RE.findall(ja))
    cue = len(CHIZURU_RE.findall(ja))
    s = 2.0 * female + 0.4 * polite + 0.8 * cue - 2.5 * male
    if male > 0:
        tier = "X"
    elif female > 0:
        tier = "A"
    elif polite > 0:
        tier = "B"
    else:
        tier = "C"
    return s, male, female, cue, tier


def evaluate():
    ep1 = json.loads((OUT / "S01E01.asr.json").read_text(encoding="utf-8"))
    seeds = [json.loads(l) for l in open(r"E:\test\rentagirl\work\chizuru_seed_v1.jsonl", encoding="utf-8")]
    asr = [json.loads(l) for l in open(r"E:\test\rentagirl\work\asr_ja.jsonl", encoding="utf-8")]
    KAZUYA = [0, 2, 4, 6, 7, 13, 16, 26, 79, 83, 89, 148, 210, 211, 240, 241, 242, 243, 244,
              245, 246, 247, 248, 249, 250, 251, 252, 253, 254, 255, 256, 269, 279, 280, 281, 282, 283]

    def near(ts):
        return [l for l in ep1 if l["start"] - 0.4 <= ts <= l["end"] + 0.9]

    pos = [l for s in seeds if s["conf"] == "high" for l in near(s["ts"])]
    neg = [l for i in KAZUYA if i < len(asr) for l in near(asr[i]["start"])]

    def rate(lines, tiers):
        return sum(1 for l in lines if score(l["ja"])[4] in tiers) / max(1, len(lines))

    for tiers in (("A",), ("A", "B")):
        print(f"tiers {tiers}: 千鹤线命中 {rate(pos, tiers):.2f}, 和也误判 {rate(neg, tiers):.2f}")
    keep_pos = sum(1 for l in pos if score(l["ja"])[4] in ("A", "B"))
    print(f"正样本 {len(pos)} 行，保留 {keep_pos}；负样本 {len(neg)} 行，误留 "
          f"{sum(1 for l in neg if score(l['ja'])[4] in ('A','B'))}")
    print("\ntier 分布（全剧 17k 行）:")
    cnt = collections.Counter()
    for f in OUT.glob("S*E*.asr.json"):
        for l in json.loads(f.read_text(encoding="utf-8")):
            cnt[score(l["ja"])[4]] += 1
    print(dict(cnt))


def build():
    rows = []
    for f in sorted(OUT.glob("S*E*.asr.json")):
        ep = f.stem.replace(".asr", "")
        for l in json.loads(f.read_text(encoding="utf-8")):
            s, male, female, cue, tier = score(l["ja"])
            if tier in ("A", "B"):
                rows.append({"ep": ep, "start": l["start"], "end": l["end"], "ja": l["ja"],
                             "tier": tier, "score": round(s, 1), "male": male,
                             "female": female, "cue": cue})
    with open(OUT / "chizuru_text.jsonl", "w", encoding="utf-8") as g:
        for r in rows:
            g.write(json.dumps(r, ensure_ascii=False) + "\n")
    a = sum(1 for r in rows if r["tier"] == "A")
    print(f"kept {len(rows)} (A={a}, B={len(rows)-a}) of 17140")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "build":
        build()
    else:
        evaluate()
        build()
