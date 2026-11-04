"""让她逛 B 站：挑视频 → 读信息 → 写评论 →（可选）发布。
用法:
  python bili_act.py --home 3            # 首页第 4 个视频，只生成草稿
  python bili_act.py --video BVxxxx      # 指定视频
  python bili_act.py --home 0 --post     # 生成并发布
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
LOG.parent.mkdir(parents=True, exist_ok=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", default="")
    ap.add_argument("--home", type=int, default=-1)
    ap.add_argument("--search", default="")
    ap.add_argument("--post", action="store_true")
    args = ap.parse_args()

    b = Bili()
    try:
        print("logged in:", b.logged_in(), flush=True)
        info = None
        if args.video:
            url = args.video if args.video.startswith("http") else f"https://www.bilibili.com/video/{args.video}"
            info = b.open_video(url)
        else:
            if args.search:
                titles = b.search(args.search)
                print("搜索结果:", titles[:5], flush=True)
                return
            idx = max(0, args.home)
            b.goto("https://www.bilibili.com")
            time.sleep(2)
            links = b.page.eval_on_selector_all(
                "a.bili-video-card__image--link, a[href*='/video/BV']",
                "els => els.map(e => e.href).filter(h => h.includes('/video/BV')).slice(0, 20)")
            if not links:
                print("没抓到视频链接")
                return
            url = links[min(idx, len(links) - 1)]
            print("打开:", url, flush=True)
            info = b.open_video(url)
        print("标题:", info["title"], flush=True)
        print("BV:", info["bvid"], flush=True)

        c = brain.comment(info["title"], info["desc"])
        print("评论(日):", c["ja"], flush=True)
        print("评论(中):", c["zh"], flush=True)

        rec = {"time": time.strftime("%Y-%m-%d %H:%M:%S"), "url": info["url"],
               "bvid": info["bvid"], "title": info["title"], "comment_ja": c["ja"],
               "comment_zh": c["zh"], "posted": False}
        if args.post:
            text = c["ja"] + ("\n" + c["zh"] if c["zh"] else "")
            ok, msg = b.post_comment(text)
            print("发布:", ok, msg, flush=True)
            rec["posted"] = bool(ok)
            rec["post_msg"] = msg
        with LOG.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        print("已记录到", LOG, flush=True)
    finally:
        b.close()


if __name__ == "__main__":
    main()
