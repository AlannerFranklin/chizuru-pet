"""她自己运营 B 站账号：定时逛、点赞、收藏、发评论（有配额和内容过滤）。
用法:
  python bili_auto.py --once --post     # 跑一次并发布
  python bili_auto.py --loop            # 常驻，按间隔自动跑
"""
import argparse
import json
import pathlib
import random
import re
import sys
import time

sys.path.insert(0, str(pathlib.Path(r"E:\RentAGirl\pet")))
sys.path.insert(0, str(pathlib.Path(r"E:\RentAGirl\tools")))
import brain  # noqa: E402
from bili_bot import Bili  # noqa: E402

ROOT = pathlib.Path(r"E:\RentAGirl")
OUT = ROOT / "out"
LOG = OUT / "bili_log.jsonl"
STATE = OUT / "bili_auto_state.json"

MAX_PER_DAY = 3
MIN_INTERVAL_H = 2.5

# 内容红线：政治、骂人、引流、敏感
BANNED = re.compile(
    r"(习近平|共产党|政治|政府|中共|台湾|香港独立|台独|藏独|疆独|六四|法轮|民主|选举|体制|"
    r"傻逼|傻b|sb|智障|脑残|去死|滚|垃圾|废物|狗东西|操你|妈的|草泥马|"
    r"http|www\.|微信|加群|QQ群|私信|代刷|广告)")
INSULT = re.compile(r"(バカ|アホ|死ね|きもい|うざい|クソ)")


def load_state():
    try:
        return json.loads(STATE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_state(d):
    STATE.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")


def today():
    return time.strftime("%Y-%m-%d")


def can_run():
    st = load_state()
    if st.get("date") != today():
        st = {"date": today(), "posts": 0, "last_ts": 0}
        save_state(st)
    if st.get("posts", 0) >= MAX_PER_DAY:
        return False, "今天已达上限"
    last = st.get("last_ts", 0)
    if time.time() - last < MIN_INTERVAL_H * 3600:
        return False, f"距上次不到 {MIN_INTERVAL_H} 小时"
    return True, "ok"


def safe(text):
    if not text or len(text) < 4:
        return False
    if BANNED.search(text) or INSULT.search(text):
        return False
    if len(text) > 120:
        return False
    return True


def run_once(post=False):
    ok, why = can_run()
    if not ok:
        print("跳过：", why, flush=True)
        return None

    b = Bili()
    rec = {"time": time.strftime("%Y-%m-%d %H:%M:%S"), "posted": False}
    try:
        if not b.logged_in():
            print("未登录，跳过", flush=True)
            return None

        w = brain.wanted_search(avoid=recent_keywords())
        print(f"她想搜：{w['keyword']}", flush=True)
        b.goto(f"https://search.bilibili.com/all?keyword={w['keyword']}", wait=3)
        time.sleep(2)
        links = b.page.eval_on_selector_all(
            "a[href*='/video/BV']",
            "els => Array.from(new Set(els.map(e => e.href))).filter(h => h.includes('/video/BV')).slice(0, 10)")
        if not links:
            print("没结果", flush=True)
            return None
        random.shuffle(links)

        info = b.open_video(links[0])
        print("看：", info["title"], flush=True)
        rec.update({"keyword": w["keyword"], "title": info["title"], "url": info["url"]})

        # 点赞
        rec["liked"] = b.like()
        # 收藏（每 2 次会话才收一次，避免堆太多）
        st = load_state()
        if st.get("posts", 0) % 2 == 0:
            rec["faved"] = b.favorite()
        else:
            rec["faved"] = None

        c = brain.comment(info["title"], info["desc"])
        ja, zh = c.get("ja", "").strip(), c.get("zh", "").strip()
        print("评论(日):", ja, flush=True)
        print("评论(中):", zh, flush=True)

        if post:
            if not (safe(ja) and safe(zh)):
                print("内容过滤未通过，只记录不发", flush=True)
            else:
                ok, msg = b.post_comment(ja + ("\n" + zh if zh else ""))
                print("发布:", ok, msg, flush=True)
                rec["posted"] = bool(ok)
                rec["post_msg"] = msg
                if ok:
                    st["posts"] = st.get("posts", 0) + 1
                    st["last_ts"] = time.time()
                    save_state(st)

        rec.update({"comment_ja": ja, "comment_zh": zh})
        with LOG.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        return rec
    finally:
        b.close()


def recent_keywords(n=6):
    try:
        kws = []
        for line in LOG.read_text(encoding="utf-8").splitlines()[-n:]:
            r = json.loads(line)
            if r.get("keyword"):
                kws.append(r["keyword"])
        return kws
    except Exception:
        return []


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--once", action="store_true")
    ap.add_argument("--post", action="store_true")
    ap.add_argument("--loop", action="store_true")
    args = ap.parse_args()

    if args.loop:
        print("自动运营已启动：每 2.5~3.5 小时一次，每天最多 3 次", flush=True)
        while True:
            try:
                run_once(post=True)
            except Exception as e:
                print("会话失败:", type(e).__name__, e, flush=True)
            wait = random.uniform(2.5, 3.5) * 3600
            print(f"下一次：{wait/3600:.1f} 小时后", flush=True)
            time.sleep(wait)
    else:
        print(json.dumps(run_once(post=args.post), ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
