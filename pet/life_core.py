"""千鹤的「生活循环」：每隔一段时间自己醒来，决定做什么，做完继续睡。
用法: python life.py --once        # 跑一次（调试）
      python life.py               # 常驻
"""
import argparse
import json
import pathlib
import random
import subprocess
import sys
import time

ROOT = pathlib.Path(r"E:\RentAGirl")

sys.path.insert(0, str(ROOT / "tools"))

MEM = ROOT / "memory"
MEM.mkdir(parents=True, exist_ok=True)
STATE = MEM / "life_state.json"
LOG = ROOT / "out" / "life_log.jsonl"
DIARY = ROOT / "workspace" / "chizuru" / "diary.md"
WECHAT_CLI = r"E:\dsh\profiles\desktop\node_modules\dsh-wechat-plugin\cli.js"

ACTIONS = {
    "bili_browse": "去 B 站看看（自己挑内容）",
    "bili_comment": "在当前视频发一条评论",
    "write_diary": "写一小段日记",
    "message_user": "主动给他发条微信",
    "rest": "什么都不做，歇一会儿",
    "study": "读台词/练声（用工作区记录）",
}


def load_state():
    try:
        return json.loads(STATE.read_text(encoding="utf-8"))
    except Exception:
        return {"energy": 70, "mood": "平静", "last_wake": 0, "last_msg": 0,
                "today_msgs": 0, "day": "", "entries": []}


def save_state(s):
    STATE.write_text(json.dumps(s, ensure_ascii=False, indent=1), encoding="utf-8")


def log(rec):
    with LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def wechat_send(text):
    try:
        r = subprocess.run(["node", WECHAT_CLI, text], capture_output=True, text=True,
                           encoding="utf-8", timeout=90, creationflags=0x08000000)
        return r.returncode == 0
    except Exception:
        return False


def scene(s, now):
    h = now.tm_hour
    part = ("深夜" if h < 6 else "早上" if h < 10 else "白天" if h < 17 else "傍晚" if h < 20 else "晚上")
    return (f"现在是 {now.tm_mon}月{now.tm_mday}日 {h:02d}:{now.tm_min:02d}（{part}）。\n"
            f"你的精力：{s['energy']}/100，心情：{s['mood']}。\n"
            f"上一次你做的事：{s.get('last_action') or '（还没做过）'}。\n")


def decide(s, now):
    import brain
    cfg = brain._load_config()
    if not cfg:
        return {"actions": ["rest"], "why": "没有模型配置"}

    sys_prompt = brain._system_prompt() + "\n\n" + (brain.memory_block() or "")
    sys_prompt += ("\n\n你正在过自己的日子，没有人跟你说话。你可以自己决定做点什么，也可以什么都不做。"
                   "不要每次都行动，一天真正做点事两三次就够了。")
    act_list = "\n".join(f"- {k}: {v}" for k, v in ACTIONS.items())
    user = (scene(s, now) +
            f"\n你现在可以做：\n{act_list}\n\n"
            "选 0~2 个动作，按先后顺序。必须只输出 JSON："
            '{"actions": ["动作名", ...], "why": "一句话理由", "mood": "此刻心情", '
            '"message": "如果选了 message_user，这里写要发的微信内容（中文，1~2 句，口语）"}')
    try:
        content = brain._request_once(cfg, [
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": user}])
        return json.loads(content)
    except Exception as e:
        print("decide failed:", type(e).__name__, str(e)[:120], flush=True)
        return {"actions": ["rest"], "why": "算了"}


def do_action(name, decision, s, now):
    import brain
    import actions as A
    res = ""
    if name == "bili_browse":
        r = brain.reply_agent("你自己去 B 站逛逛，挑一个你想看的，看完说说感受。")
        res = (r or {}).get("zh", "") or "逛了一圈"
        s["energy"] = max(0, s["energy"] - 12)
    elif name == "bili_comment":
        cur = A.STATE.get("current")
        if cur:
            c = brain.comment(cur.get("title", ""), cur.get("desc", ""))
            ok = A.call("bili_comment", {"text": c.get("ja", "")})
            res = f"评论：{ok}"
        else:
            res = "还没打开视频，先逛了逛"
            brain.reply_agent("你自己去 B 站随便看看。")
        s["energy"] = max(0, s["energy"] - 8)
    elif name == "write_diary":
        try:
            cfg = brain._load_config()
            sys_p = brain._system_prompt() + "\n\n现在你在写日记，不是在跟人说话：用第一人称、简短、诚实，3~5 句中文，不要写称呼。"
            content = brain._request_once(cfg, [
                {"role": "system", "content": sys_p},
                {"role": "user", "content": "写今天的日记。只输出 JSON：{\"diary\": \"正文\"}"}])
            import re as _re
            m = _re.search(r"\{.*\}", content, _re.S)
            obj = json.loads(m.group(0) if m else content)
            line = obj.get("diary") or content
            with DIARY.open("a", encoding="utf-8") as f:
                f.write(f"\n## {now.tm_mon}/{now.tm_mday} {now.tm_hour:02d}:{now.tm_min:02d}\n{line}\n")
            res = "写了一小段日记"
        except Exception as e:
            res = f"日记没写成：{e}"
    elif name == "message_user":
        msg = (decision.get("message") or "").strip()
        if not msg:
            msg = "……在吗？没什么事，就是随口问一句"
        ok = wechat_send(msg)
        if ok:
            s["last_msg"] = time.time()
            s["today_msgs"] = s.get("today_msgs", 0) + 1
        res = f"发微信：{'成功' if ok else '失败'}｜{msg}"
    elif name == "study":
        try:
            brain.reply_agent("练一会儿台词：自己挑一句台词，读一读，说说感觉。")
            res = "练了一会儿台词"
        except Exception:
            res = "练台词"
        s["energy"] = max(0, s["energy"] - 5)
    else:
        res = "什么都没做"
        s["energy"] = min(100, s["energy"] + 15)
    return res


def can_message(s, now):
    if s.get("day") != time.strftime("%Y-%m-%d"):
        s["today_msgs"] = 0
        s["day"] = time.strftime("%Y-%m-%d")
    if not (8 <= now.tm_hour < 23):
        return False
    if s.get("today_msgs", 0) >= 2:
        return False
    if time.time() - s.get("last_msg", 0) < 6 * 3600:
        return False
    return True


def wake_once():
    import brain
    s = load_state()
    now = time.localtime()
    d = decide(s, now)
    names = [a for a in d.get("actions", []) if a in ACTIONS][:2]
    if "message_user" in names and not can_message(s, now):
        names = [n for n in names if n != "message_user"] or ["rest"]
    results = []
    for n in names:
        try:
            results.append(f"{n} → {do_action(n, d, s, now)}")
        except Exception as e:
            results.append(f"{n} 失败：{type(e).__name__}")
    s["mood"] = d.get("mood") or s.get("mood", "平静")
    s["energy"] = max(0, min(100, s["energy"] + random.randint(-3, 3)))
    s["last_wake"] = time.time()
    s["last_action"] = "；".join(results)[:200]
    s["entries"] = (s.get("entries", []) + [f"{now.tm_mon}/{now.tm_mday} {now.tm_hour:02d}:{now.tm_min:02d} {s['last_action']}"])[-30:]
    save_state(s)
    rec = {"t": time.strftime("%Y-%m-%d %H:%M:%S"), "why": d.get("why", ""),
           "actions": names, "results": results, "energy": s["energy"], "mood": s["mood"]}
    log(rec)
    print(json.dumps(rec, ensure_ascii=False), flush=True)
    return rec


