import json, pathlib, random

OUT = pathlib.Path(r"E:\RentAGirl\out")
rows = [json.loads(l) for l in (OUT / "chizuru_gold.jsonl").open(encoding="utf-8")]
ok = [r for r in rows if r["conf"] == "high" and 4 <= len(r["ja"]) <= 30]

want = {"素": 14, "営業": 12, "衝突": 12, "软肋": 3}
out = []
for mode, n in want.items():
    pool = [r for r in ok if r["mode"] == mode]
    pool.sort(key=lambda r: len(r["ja"]))
    # 取短句里均匀分布的 n 条
    step = max(1, len(pool) // n)
    pick = pool[::step][:n]
    out.append(f"### {mode}（共 {len(pool)} 条可用）")
    for r in pick:
        zh = r.get("zh") or ""
        out.append(f"{r['ja']}" + (f"   || {zh}" if zh else ""))
    out.append("")

(OUT / "fewshot_candidates.txt").write_text("\n".join(out), encoding="utf-8")
print("written", len(ok))
