import json, pathlib, re, collections

REPO = pathlib.Path(r"E:\RentAGirl")
OUT = REPO / "out"

MALE = re.compile(r"(俺|おれ|僕|ぼく|だぜ|かよ|んだよ|してんじゃねえ|すんのか|やめろ|だろーが)")
KEIGO = re.compile(r"(です|ます|ございます|お客様|よろしく|ありがとうございます|申し訳)")
CONFLICT = re.compile(r"(バカ|ばか|通報|事務所|契約|そんなわけ|ふざけ|脱線|営業妨害|天地が)")
SOFT = re.compile(r"(ばあちゃん|おばあちゃん|寂し|夢|芝居|舞台|オーディション)")


def mode(ja):
    if CONFLICT.search(ja):
        return "衝突"
    if SOFT.search(ja):
        return "软肋"
    if KEIGO.search(ja):
        return "営業"
    return "素"


rows = []
per = {}
for f in sorted(OUT.glob("S*E*.f0.jsonl")):
    ep = f.stem.replace(".f0", "")
    n = 0
    for line in f.open(encoding="utf-8"):
        r = json.loads(line)
        if not r["female"] or MALE.search(r["ja"]):
            continue
        if len(r["ja"]) < 2:
            continue
        r.pop("female", None)
        r["ep"] = ep
        r["mode_guess"] = mode(r["ja"])
        rows.append(r)
        n += 1
    per[ep] = n

with open(OUT / "chizuru_candidates.jsonl", "w", encoding="utf-8") as g:
    for r in rows:
        g.write(json.dumps(r, ensure_ascii=False) + "\n")

modes = collections.Counter(r["mode_guess"] for r in rows)
print(f"episodes={len(per)} candidates={len(rows)}")
print("modes:", dict(modes))
print("per-ep min/max:", min(per.values()), max(per.values()), "median:", sorted(per.values())[len(per)//2])
print("\n--- 20 samples ---")
for r in rows[:: max(1, len(rows) // 20)][:20]:
    print(f"{r['ep']} {r['start']:6.1f} [{r['mode_guess']}] {r['ja'][:50]}")
