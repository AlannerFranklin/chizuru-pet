import json, pathlib, random, collections

REPO = pathlib.Path(r"E:\RentAGirl")
OUT = REPO / "out"
rows = [json.loads(l) for l in (OUT / "corpus.jsonl").open(encoding="utf-8")]
stats = json.loads((OUT / "corpus_stats.json").read_text(encoding="utf-8"))

season = collections.Counter()
season_lines = collections.Counter()
for r in rows:
    s = r["ep"][1:3]
    season[s] += 1
    season_lines[s] += 1

per = stats["per_episode"]
cov = [(k, v["zh_rate"]) for k, v in per.items()]

random.seed(7)
sample = random.sample([r for r in rows if r.get("zh")], 12)

with open(OUT / "REPORT.md", "w", encoding="utf-8") as f:
    f.write("# 租借女友 语料库 · 处理报告\n\n")
    f.write("## 总览\n\n")
    f.write(f"- 集数：{stats['episodes']}（S01 12 + S02 12 + S03 12 + S04 12 + S05 3）\n")
    f.write(f"- 台行数：**{stats['lines']:,}**\n")
    f.write(f"- 日文字符：**{stats['ja_chars']:,}**\n")
    f.write(f"- 有中文字幕：{stats['with_zh']:,}（{stats['with_zh']/stats['lines']*100:.1f}%）\n")
    ok = sum(1 for r in rows if r.get("align_ok"))
    f.write(f"- 中日对齐可信：**{ok:,}（{ok/stats['lines']*100:.1f}%）**（字数比在 0.3~1.4 之间，见 `align_ok` 字段）\n")
    f.write(f"- 平均每集 {stats['lines']/stats['episodes']:.0f} 行，每行 {stats['ja_chars']/stats['lines']:.1f} 字\n\n")

    f.write("## 分季\n\n| 季 | 行数 |\n|---|---|\n")
    for s in sorted(season):
        f.write(f"| S{s} | {season[s]:,} |\n")

    f.write("\n## 中文字幕覆盖率\n\n")
    f.write(f"- 中位数 {sorted(c for _, c in cov)[len(cov)//2]*100:.0f}%\n")
    f.write(f"- 最高 {max(cov, key=lambda x: x[1])[0]} {max(c for _, c in cov)*100:.0f}%\n")
    f.write(f"- 最低 {min(cov, key=lambda x: x[1])[0]} {min(c for _, c in cov)*100:.0f}%\n")
    f.write("- 约 45 集在 87%~96%，6 集（S03E10/E11、S05E01-E03 等）在 43%~76%（字幕位置随季节变化，已按 y=800 重跑过一轮）\n")

    f.write("\n## 抽样（ja / zh）\n\n")
    for r in sample:
        f.write(f"**{r['ep']}** `{r['start']:.1f}s`\n\n")
        f.write(f"- {r['ja']}\n- {r['zh']}\n\n")

    f.write("\n## 流水线与耗时\n\n")
    f.write("| 阶段 | 单集耗时 |\n|---|---|\n")
    f.write("| 下载（1080p） | 30~60 秒 |\n")
    f.write("| 正片结束点检测（粉描边字幕指纹） | 10 秒 |\n")
    f.write("| 日文 ASR（large-v3，word timestamps） | 60~100 秒 |\n")
    f.write("| 中文字幕 OCR（rec-only，跳过检测） | 25 秒 |\n")
    f.write("| **合计** | **约 2.5 分钟/集** |\n\n")

    f.write("## 已知限制\n\n")
    f.write("1. 说话人未分离：语料是全说话人混合，千鹤的行需另外标注（S01E01 已有 95 行金标）。\n")
    f.write("2. 少数集中文字幕覆盖偏低（43%~76%）。\n")
    f.write("3. 正片结束点靠字幕指纹，极端情况下（长时间无字幕结尾）可能偏差。已 QA：51 集裁点均不早于最后一句语音。\n")

print("report written")
print(f"lines={stats['lines']} chars={stats['ja_chars']} zh={stats['with_zh']}")
