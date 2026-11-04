"""对还没有人工金标的集：自动标「千鹤候选」，conf=auto。
规则：声纹相似度 >= TH 且不含明显他人语体；mode 用文本规则猜。
输出 out/chizuru_auto.jsonl（每行带 ep/score/mode）
"""
import json, pathlib, re
import numpy as np

OUT = pathlib.Path(r"E:\RentAGirl\out")
TH = 0.50
BAD = re.compile(r"(カズヤさん|俺|おれ|僕|ぼく|だぜ|かよ|てめえ|ふざけんな|あたし)")
KEIGO = re.compile(r"(です|ます|ございます|お客様|指名料|料金)")
CONFLICT = re.compile(r"(バカ|通報|事務所|契約|そんなわけ|ふづけ|営業妨害|天地が|勘違い)")
SOFT = re.compile(r"(ばあちゃん|おばあちゃん|夢|芝居|舞台|オーディション|母さん|父さん)")

C = np.load(OUT / "enroll_all.npy")


def mode_of(ja):
    if CONFLICT.search(ja):
        return "衝突"
    if SOFT.search(ja):
        return "软肋"
    if KEIGO.search(ja):
        return "営業"
    return "素"


def main():
    gold_eps = {json.loads(l)["ep"] for l in (OUT / "chizuru_gold.jsonl").open(encoding="utf-8")}
    rows = []
    for emb_path in sorted(OUT.glob("S*.lineemb.npy")):
        ep = emb_path.name.replace(".lineemb.npy", "")
        if ep in gold_eps:
            continue
        lines = json.loads((OUT / f"{ep}.asr.json").read_text(encoding="utf-8"))
        E = np.load(emb_path)
        sims = E @ C
        for i, l in enumerate(lines):
            if sims[i] >= TH and not BAD.search(l["ja"]):
                rows.append({"ep": ep, "start": l["start"], "end": l["end"], "ja": l["ja"],
                             "mode": mode_of(l["ja"]), "score": round(float(sims[i]), 3), "conf": "auto"})
    with open(OUT / "chizuru_auto.jsonl", "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print("auto lines:", len(rows), "from", len({r['ep'] for r in rows}), "episodes")


if __name__ == "__main__":
    main()
