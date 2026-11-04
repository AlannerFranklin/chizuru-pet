"""让她按自己的兴趣逛 B 站：想搜什么 → 搜索 → 打开第一条 → 写评论。
用法:
  python bili_will.py              # 只生成草稿
  python bili_will.py --post       # 生成并发布
"""
import argparse
import json
import pathlib
import sys
import time

sys.path.insert(0, str(pathlib.Path(r"E:\RentAGirl\pet")))
sys.path.insert(0, str(pathlib.Path(r"E:\RentAGirl\tools")))
import brain  # noqa: E402
from bili_bot import Bili  # noqa: E402

LOG = pathlib.Path(r"E:\RentAGirl\out\bili_log.jsonl")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--post", action="store_true")
    ap.add_argument("--keyword", default="")
    args = ap.parse_args()

    b = Bili()
    try:
        print("logged in:", b.logged_in(), flush=True)
        if args.keyword:
            kw, why = args.keyword, ""
        else:
            w = brain.wanted_search()
            kw, why = w["keyword"], w["why"]
            print(f"她想搜：{kw}  （{why}）", flush=True)

        url = f"https://search.bilibili.com/all?keyword={kw}"
        b.goto(url, wait=3)
        time.sleep(2)
        links = b.page.eval_on_selector_all(
            "a[href*='/video/BV']",
            "els => Array.from(new Set(els.map(e => e.href))).slice(0, 10)")
        print("搜到", len(links), "个视频", flush=True)
        if not links:
            print("没搜到结果")
            return
        target = links[0]
        info = b.open_video(target)
        print("打开:", info["title"] or info["url"], flush=True)

        c = brain.comment(info["title"], info["desc"])
        print("评论(日):", c["ja"], flush=True)
        print("评论(中):", c["zh"], flush=True)

        rec = {"time": time.strftime("%Y-%m-%d %H:%M:%S"), "keyword": kw,
               "url": info["url"], "title": info["title"],
               "comment_ja": c["ja"], "comment_zh": c["zh"], "posted": False}
        if args.post:
            ok, msg = b.post_comment(c["ja"] + ("\n" + c["zh"] if c["zh"] else ""))
            print("发布:", ok, msg, flush=True)
            rec["posted"] = bool(ok)
            rec["post_msg"] = msg
        with LOG.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    finally:
        b.close()


if __name__ == "__main__":
    main()
