"""让她一次逛好一会儿：首页/热门/分区/搜索，看多条，最后用自己的话总结。
用法: python bili_session.py [--rounds 3] [--post] [--zone 动画|音乐|舞蹈|生活|知识|影视]
"""
import argparse
import json
import pathlib
import random
import sys
import time

sys.path.insert(0, str(pathlib.Path(r"E:\RentAGirl\pet")))
sys.path.insert(0, str(pathlib.Path(r"E:\RentAGirl\tools")))
import brain  # noqa: E402
from bili_bot import Bili  # noqa: E402

LOG = pathlib.Path(r"E:\RentAGirl\out\bili_log.jsonl")

ZONES = {
    "动画": "https://www.bilibili.com/v/douga/",
    "音乐": "https://www.bilibili.com/v/music/",
    "舞蹈": "https://www.bilibili.com/v/dance/",
    "生活": "https://www.bilibili.com/v/life/",
    "知识": "https://www.bilibili.com/v/knowledge/",
    "影视": "https://www.bilibili.com/v/cinephile/",
}


def collect_links(page, limit=12):
    return page.eval_on_selector_all(
        "a[href*='/video/BV']",
        f"els => Array.from(new Set(els.map(e => e.href))).filter(h => h.includes('/video/BV')).slice(0, %d)" % limit)


LAST = pathlib.Path(r"E:\RentAGirl\out\bili_last.json")


def load_last():
    try:
        d = json.loads(LAST.read_text(encoding="utf-8"))
        return set(d.get("urls", [])), d.get("titles", [])
    except Exception:
        return set(), []


def save_last(urls, titles):
    try:
        LAST.write_text(json.dumps({"urls": list(urls)[-20:], "titles": titles[-8:]},
                                   ensure_ascii=False, indent=1), encoding="utf-8")
    except Exception:
        pass


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rounds", type=int, default=3)
    ap.add_argument("--post", action="store_true")
    ap.add_argument("--zone", default="")
    args = ap.parse_args()

    b = Bili()
    watched = []
    try:
        print("logged in:", b.logged_in(), flush=True)
        if args.zone and args.zone in ZONES:
            b.goto(ZONES[args.zone], wait=3)
            print(f"进了{args.zone}区", flush=True)
            links = collect_links(b.page)
        elif random.random() < 0.4:
            zone = random.choice(list(ZONES))
            b.goto(ZONES[zone], wait=3)
            print(f"随手进了{zone}区", flush=True)
            links = collect_links(b.page)
        else:
            avoid = []
            try:
                for line in LOG.read_text(encoding="utf-8").splitlines()[-8:]:
                    r = json.loads(line)
                    if r.get("keyword"):
                        avoid.append(r["keyword"])
            except Exception:
                pass
            w = brain.wanted_search(avoid=avoid)
            print(f"她想搜：{w['keyword']}（{w['why']}）", flush=True)
            b.goto(f"https://search.bilibili.com/all?keyword={w['keyword']}", wait=3)
            time.sleep(2)
            links = collect_links(b.page)

        avoided, _prev_titles = load_last()
        links = [u for u in links if u.split("?")[0] not in {x.split("?")[0] for x in avoided}]
        if not links:
            print("没抓到视频")
            return
        random.shuffle(links)
        for i, url in enumerate(links[: args.rounds]):
            try:
                info = b.open_video(url)
                if not info.get("title"):
                    continue
                watched.append(info)
                print(f"[{i+1}] {info['title']}", flush=True)
                time.sleep(1)
            except Exception as e:
                print("跳过:", type(e).__name__, flush=True)

        if not watched:
            print("啥也没看成")
            return

        # 让她总结这次逛的感受，并对最有意思的一条写评论
        titles = "\n".join(f"- {w['title']}" for w in watched)
        summary = brain.reply(
            "你刚在B站刷到并点开了下面这些视频，随便看看而已：\n" + titles +
            "\n用一句话说说你点开后的感受（可以吐槽、好奇、想继续看、或者觉得没意思），"
            "就像平常跟人聊天那样，别像在汇报。"
        )
        print("感受:", summary.get("ja"), "|", summary.get("zh"), flush=True)

        target = watched[0]
        c = brain.comment(target["title"], target.get("desc", ""))
        print("评论(日):", c["ja"], flush=True)
        print("评论(中):", c["zh"], flush=True)

        rec = {"time": time.strftime("%Y-%m-%d %H:%M:%S"),
               "watched": [w["title"] for w in watched],
               "summary_ja": summary.get("ja", ""), "summary_zh": summary.get("zh", ""),
               "comment_target": target["title"], "comment_ja": c["ja"],
               "comment_zh": c["zh"], "posted": False}

        if args.post:
            b.open_video(target["url"])
            ok, msg = b.post_comment(c["ja"] + ("\n" + c["zh"] if c["zh"] else ""))
            print("发布:", ok, msg, flush=True)
            rec["posted"] = bool(ok)
            rec["post_msg"] = msg

        with LOG.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        save_last(avoided | {w["url"].split("?")[0] for w in watched},
                  [w["title"] for w in watched])

        print("SUMMARY_JA:" + summary.get("ja", ""), flush=True)
        print("SUMMARY_ZH:" + summary.get("zh", ""), flush=True)
    finally:
        b.close()


if __name__ == "__main__":
    main()
