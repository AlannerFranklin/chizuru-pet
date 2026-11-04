"""千鹤的大脑。
- 有 pet/config.json（base_url + api_key + model）→ 调 LLM
- 没有 → 用金标语料做占位应答
输出统一：{"ja": 日文, "zh": 中文, "mode": 素/営業/衝突/软肋}
"""
import json
import pathlib
import pathlib
import random
import re
import guard

ROOT = pathlib.Path(__file__).resolve().parent.parent
GOLD = ROOT / "out" / "chizuru_gold.jsonl"
CARD = ROOT / "card_v0_4.md"
CONFIG = pathlib.Path(__file__).resolve().parent / "config.json"

_rows = []
if GOLD.exists():
    _rows = [json.loads(l) for l in GOLD.open(encoding="utf-8")]
_by_mode = {}
for r in _rows:
    _by_mode.setdefault(r["mode"], []).append(r)

RULES = [
    (re.compile(r"(疲れ|つかれ|だるい|しんど|眠い|ねむい)"), "素"),
    (re.compile(r"(好き|すき|付き合|つきあ|結婚|けっこん|彼女)"), "衝突"),
    (re.compile(r"(可愛|かわい|綺麗|きれい|似合)"), "営業"),
    (re.compile(r"(ばあちゃん|おばあちゃん|家族|かぞく|夢|ゆめ|母|父)"), "软肋"),
    (re.compile(r"(演技|えんぎ|舞台|ぶたい|オーディション|女優)"), "素"),
]

_MEM_FILE = pathlib.Path(r"E:\RentAGirl\memory\memory.json")
_MEM_FILE.parent.mkdir(parents=True, exist_ok=True)
MEMORY = {"summary": "", "facts": [], "history": []}
MAX_TURNS = 14          # 超过就压缩老对话
KEEP_TURNS = 6          # 压缩后保留最近几轮原文


def _load_memory():
    global MEMORY
    try:
        d = json.loads(_MEM_FILE.read_text(encoding="utf-8"))
        MEMORY = {"summary": d.get("summary", ""), "facts": d.get("facts", []) or [],
                  "history": [(str(u), str(a)) for u, a in d.get("history", [])]}
    except Exception:
        MEMORY = {"summary": "", "facts": [], "history": []}


def _save_memory():
    try:
        _MEM_FILE.write_text(json.dumps({
            "summary": MEMORY["summary"],
            "facts": MEMORY["facts"][-60:],
            "history": [list(x) for x in MEMORY["history"][-60:]],
        }, ensure_ascii=False, indent=1), encoding="utf-8")
    except Exception as e:
        print("save memory failed:", e)


def remember_fact(fact):
    fact = (fact or "").strip()
    if fact and fact not in MEMORY["facts"]:
        MEMORY["facts"].append(fact)
        _save_memory()


def _compress_if_needed():
    """历史太长时，把较早的对话压成一段摘要（后台线程里跑）。"""
    if len(MEMORY["history"]) <= MAX_TURNS:
        return
    cfg = _load_config()
    old = MEMORY["history"][:-KEEP_TURNS]
    if not old or not cfg:
        return
    lines = "\n".join(f"他：{u}\n你：{a}" for u, a in old)
    prompt = (
        "把下面这段对话压缩成 5 条以内的事实/关系摘要，用中文，第三人称，"
        "只写长期有用的信息（他喜欢什么、发生过什么、你的态度），不要客套。\n"
        "只输出 JSON：{\"summary\": \"摘要文本\"}\n\n"
        + lines[:6000]
    )
    try:
        content = _request_once(cfg, [
            {"role": "system", "content": "你是一个简洁的记忆压缩器。"},
            {"role": "user", "content": prompt}])
        if content:
            txt = content.strip()
            try:
                m = re.search(r"\{.*\}", txt, re.S)
                obj = json.loads(m.group(0) if m else txt)
                txt = obj.get("summary") or txt
            except Exception:
                pass
            MEMORY["summary"] = (MEMORY["summary"] + "\n" + txt)[-3000:]
            MEMORY["history"] = MEMORY["history"][-KEEP_TURNS:]
            _save_memory()
    except Exception as e:
        print("compress failed:", type(e).__name__, e)


def memory_block():
    parts = []
    if MEMORY["summary"]:
        parts.append("关于你们之前聊过的（摘要）：\n" + MEMORY["summary"])
    if MEMORY["facts"]:
        parts.append("你记得的事：\n" + "\n".join("- " + f for f in MEMORY["facts"][-20:]))
    return "\n\n".join(parts)


_HIST_FILE = pathlib.Path(__file__).resolve().parent / "history.json"


def _load_history():
    try:
        data = json.loads(_HIST_FILE.read_text(encoding="utf-8"))
        return [(str(u), str(a)) for u, a in data][-20:]
    except Exception:
        return []


def _save_history():
    try:
        _HIST_FILE.write_text(json.dumps(_history[-20:], ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass


_load_memory()
_history = MEMORY["history"] if MEMORY["history"] else _load_history()
MEMORY["history"] = _history   # 同一个列表，保存时才不会丢


def _pick(mode):
    pool = _by_mode.get(mode) or _rows
    if not pool:
        return {"ja": "……", "zh": "……", "mode": mode}
    r = random.choice(pool)
    return {"ja": r["ja"], "zh": r.get("zh") or "", "mode": r["mode"]}


def _load_config():
    if not CONFIG.exists():
        return None
    try:
        cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    except Exception:
        return None
    if not cfg.get("api_key") or not cfg.get("base_url"):
        return None
    return cfg


def _system_prompt():
    card = CARD.read_text(encoding="utf-8") if CARD.exists() else ""
    shot = []
    for mode in ("営業", "素", "衝突", "软肋"):
        pool = [r for r in _by_mode.get(mode, []) if r.get("conf") == "high"][:6]
        for r in pool:
            shot.append(f"[{mode}] {r['ja']} ／ {r.get('zh','')}")
    return (
        card
        + "\n\n## 输出格式（必须严格遵守）\n"
          "只输出一个 JSON 对象，不要任何解释或 Markdown：\n"
          '{"ja": "她会说的日文（1~3 句）", "zh": "对应的中文", "mode": "素|営業|衝突|软肋"}\n'
          "中文要像字幕，不要翻译腔。\n\n## 语气样本\n" + "\n".join(shot)
    )


def _call_llm(cfg, text):
    import urllib.request

    msgs = [{"role": "system", "content": _system_prompt()}]
    for u, a in _history[-6:]:
        msgs.append({"role": "user", "content": u})
        msgs.append({"role": "assistant", "content": a})
    msgs.append({"role": "user", "content": text})

    body = json.dumps({
        "model": cfg.get("model", "deepseek-chat"),
        "messages": msgs,
        "temperature": cfg.get("temperature", 0.8),
        "max_tokens": 300,
        "response_format": {"type": "json_object"},
    }).encode("utf-8")

    req = urllib.request.Request(
        cfg["base_url"].rstrip("/") + "/chat/completions",
        data=body,
        headers={"Content-Type": "application/json",
                 "Authorization": "Bearer " + cfg["api_key"]},
    )
    with urllib.request.urlopen(req, timeout=cfg.get("timeout", 30)) as r:
        data = json.loads(r.read().decode("utf-8"))
def _request_once(cfg, msgs):
    import urllib.request

    body = json.dumps({
        "model": cfg.get("model", "deepseek-chat"),
        "messages": msgs,
        "temperature": cfg.get("temperature", 0.8),
        "max_tokens": 300,
        "response_format": {"type": "json_object"},
    }, ensure_ascii=False).encode("utf-8")

    req = urllib.request.Request(
        cfg["base_url"].rstrip("/") + "/chat/completions",
        data=body,
        headers={"Content-Type": "application/json",
                 "Authorization": "Bearer " + cfg["api_key"]},
    )
    with urllib.request.urlopen(req, timeout=cfg.get("timeout", 30)) as r:
        data = json.loads(r.read().decode("utf-8"))
    return data["choices"][0]["message"]["content"].strip()


def _call_llm(cfg, text, extra=None):
    import time

    sys_text = _system_prompt()
    mem = memory_block()
    if mem:
        sys_text += "\n\n" + mem
    if extra:
        sys_text += "\n\n" + extra
    sys_msg = {"role": "system", "content": sys_text}
    hist = []
    for u, a in _history[-6:]:
        hist.append({"role": "user", "content": u})
        hist.append({"role": "assistant", "content": a})

    variants = [
        [sys_msg] + hist + [{"role": "user", "content": text}],
        [sys_msg, {"role": "user", "content": text}],
    ]
    for attempt, msgs in enumerate(variants):
        for _ in range(2):
            content = _request_once(cfg, msgs)
            if content:
                break
            time.sleep(0.5)
        if content:
            break
    if not content:
        raise ValueError("empty content from API")

    content = re.sub(r"^```(json)?|```$", "", content, flags=re.M).strip()
    try:
        obj = json.loads(content)
    except Exception:
        m = re.search(r"\{.*\}", content, re.S)
        if not m:
            raise
        obj = json.loads(m.group(0))
    return {"ja": obj.get("ja", ""), "zh": obj.get("zh", ""), "mode": obj.get("mode", "素")}


def reply(text):
    global _history
    cfg = _load_config()

    name, verified = guard.check(text)
    note = guard.guard_prompt(name) if (name and not verified) else None

    r = None
    if cfg:
        for attempt in range(2 if note else 1):
            try:
                r = _call_llm(cfg, text, extra=note)
            except Exception as e:
                print("LLM failed:", type(e).__name__, str(e)[:160], flush=True)
                r = None
            if note:
                if r and guard.needs_rewrite(r["ja"]):
                    r = None
                    continue
                break
            if r:
                break
    if r is None:
        r = dict(guard.FALLBACK) if note else _pick(
            next((m for p, m in RULES if p.search(text)), "素"))
    _history.append((text, r["ja"]))
    _save_memory()
    import threading
    threading.Thread(target=_compress_if_needed, daemon=True).start()
    return r


def idle():
    return _pick(random.choice(["素", "素", "営業"]))


def wanted_search(avoid=None):
    """以她的兴趣决定搜什么（返回关键词）。avoid: 最近看过的，避免重复。"""
    cfg = _load_config()
    avoid_txt = ""
    if avoid:
        avoid_txt = "\n最近已经看过的方向：" + "、".join(avoid[-5:]) + "\n这次换一个完全不同的方向。\n"
    prompt = (
        "现在是你在自己逛 B 站的时间。按你自己的兴趣决定搜点什么。\n"
        "你的兴趣很杂：舞台剧和演戏、演技训练、声优/动画（你干这行所以特别在意配音）、"
        "唱歌和声乐、跳舞、做饭、照顾外婆的日常、日剧和电影、偶尔想放空的搞笑视频、猫。\n"
        + avoid_txt +
        "只输出一个 JSON：{\"keyword\": \"搜索词（中文，2~8 个字，具体一点）\", \"why\": \"一句简短理由\"}"
    )
    if cfg:
        try:
            msgs = [{"role": "system", "content": _system_prompt()},
                    {"role": "user", "content": prompt}]
            content = _request_once(cfg, msgs)
            if content:
                content = re.sub(r"^```(json)?|```$", "", content, flags=re.M).strip()
                m = re.search(r"\{.*\}", content, re.S)
                obj = json.loads(m.group(0) if m else content)
                kw = (obj.get("keyword") or "").strip()
                if kw:
                    return {"keyword": kw, "why": (obj.get("why") or "").strip()}
        except Exception as e:
            print("search llm failed:", type(e).__name__, e)
    return {"keyword": random.choice(["舞台剧 片段", "声乐练习", "简单料理"]), "why": ""}


def vlog_script():
    """让她自己写一段短视频文案（30~45 秒）。"""
    cfg = _load_config()
    prompt = (
        "你要给 B 站拍一条 30~45 秒的短视频，对着镜头说话的感觉。\n"
        "内容可以是你最近在想的事、今天干了什么、对某件事的看法，真实一点，不要像广告，"
        "不要提自己是 AI、桌宠或租借女友，也不要提观众。\n"
        "5~7 句短句，每句日文 12~30 字，配中文翻译。\n"
        "只输出 JSON：{\"title\": \"视频标题\", \"lines\": [{\"ja\": \"...\", \"zh\": \"...\"}, ...]}"
    )
    if cfg:
        try:
            msgs = [{"role": "system", "content": _system_prompt()},
                    {"role": "user", "content": prompt}]
            content = _request_once(cfg, msgs)
            if content:
                content = re.sub(r"^```(json)?|```$", "", content, flags=re.M).strip()
                m = re.search(r"\{.*\}", content, re.S)
                obj = json.loads(m.group(0) if m else content)
                if obj.get("lines"):
                    return obj
        except Exception as e:
            print("vlog llm failed:", type(e).__name__, e)
    return None


def comment(video_title, video_desc=""):
    """在 B 站看到某个视频后，以她的口吻写一条评论（日文+中文）。"""
    cfg = _load_config()
    prompt = (
        "你现在在逛 B 站，看到一个视频：\n"
        f"标题：{video_title}\n"
        f"简介：{video_desc[:200]}\n\n"
        "以水原千鹤的身份写一条真实感评论：口语、短（1~2 句日文），"
        "像普通观众一样，可以吐槽/感慨/认真点评，但不要提自己是 AI、桌宠或租借女友，"
        "也不要提观众。只输出 JSON：{\"ja\": \"日文评论\", \"zh\": \"中文翻译\"}"
    )
    if cfg:
        try:
            msgs = [{"role": "system", "content": _system_prompt()},
                    {"role": "user", "content": prompt}]
            content = _request_once(cfg, msgs)
            if content:
                content = re.sub(r"^```(json)?|```$", "", content, flags=re.M).strip()
                m = re.search(r"\{.*\}", content, re.S)
                obj = json.loads(m.group(0) if m else content)
                return {"ja": obj.get("ja", ""), "zh": obj.get("zh", "")}
        except Exception as e:
            print("comment llm failed:", type(e).__name__, e)
    r = _pick("素")
    return {"ja": r["ja"], "zh": r.get("zh", "")}

# ---------------- 带工具的对话（她自己决定要不要操作） ----------------

def _request_tools(cfg, msgs, tools):
    import urllib.request

    body = json.dumps({
        "model": cfg.get("model", "deepseek-chat"),
        "messages": msgs,
        "tools": tools,
        "temperature": cfg.get("temperature", 0.8),
        "max_tokens": 500,
    }, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        cfg["base_url"].rstrip("/") + "/chat/completions",
        data=body,
        headers={"Content-Type": "application/json",
                 "Authorization": "Bearer " + cfg["api_key"]},
    )
    with urllib.request.urlopen(req, timeout=max(30, cfg.get("timeout", 30))) as r:
        data = json.loads(r.read().decode("utf-8"))
    return data["choices"][0]["message"]


_AGENT_HINT = """
你有真正的操作能力。凡是需要用动作完成的请求，必须先调用工具，再回话，不要只说不做。
硬性要求：他说"换个 / 不喜欢这个 / 不要这个 / 下一个"时，你必须先调用 bili_next，再回话。
- 他让你搜/看/换个视频 → 调 bili_search / bili_open / bili_next
- 你说好看/想看/发个评论 → 调 bili_comment（内容你自己写，日文）
- 他说不错/喜欢 → 可以 bili_like、bili_favorite
- 他说了值得记住的事 → remember 记下来
看到标题擦边/成人/引战/猎奇的，直接跳过换一个，不要点开。
你还有一个自己的工作区（E:\\RentAGirl\\workspace\\chizuru），可以用 list_dir / read_file / write_file /
run_cmd / run_python 在里面写代码、跑脚本、处理文件、做小工具，就像程序员一样。
他要你写程序、算东西、处理文件、做自动化，就直接动手做，不要说"我做不到"。
遇到复杂任务时先用 write_plan 写下步骤，再一步步执行；需要时可以 spawn_subagent 把独立子任务派给子代理；
需要查资料就 web_search / web_fetch。
工具调用完，再用你的语气回一句（JSON 格式 {"ja","zh","mode"}）。别描述工具参数，别汇报流程。
"""


def reply_agent(text):
    """带工具调用的回复：她自己决定要不要去操作。"""
    global _history
    import actions

    cfg = _load_config()
    if not cfg:
        return reply(text)

    sys_text = _system_prompt() + "\n\n" + _AGENT_HINT
    mem = memory_block()
    if mem:
        sys_text += "\n\n" + mem

    msgs = [{"role": "system", "content": sys_text}]
    for u, a in _history[-6:]:
        msgs.append({"role": "user", "content": u})
        msgs.append({"role": "assistant", "content": a})
    msgs.append({"role": "user", "content": text})

    final = ""
    for _step in range(12):
        try:
            msg = _request_tools(cfg, msgs, actions.TOOLS)
        except Exception as e:
            print("agent llm failed:", type(e).__name__, str(e)[:160])
            break

        calls = msg.get("tool_calls") or []
        if calls:
            msgs.append({"role": "assistant", "content": msg.get("content") or "",
                         "tool_calls": calls})
            for c in calls:
                name = c["function"]["name"]
                try:
                    args = json.loads(c["function"].get("arguments") or "{}")
                except Exception:
                    args = {}
                print(f"tool: {name}({args})", flush=True)
                result = actions.call(name, args)
                print("  ->", result[:120], flush=True)
                msgs.append({"role": "tool", "tool_call_id": c["id"], "content": result})
            continue

        final = (msg.get("content") or "").strip()
        break

    # 收尾：强制要一个结构化回复（工具调用的内容不直接当台词）
    r = None
    try:
        msgs.append({"role": "assistant", "content": final or "（已经做完了）"})
        msgs.append({"role": "user", "content":
                     "现在只用你的语气回他一句（不要说工具、不要汇报流程），"
                     "只输出 JSON：{\"ja\":\"日文\",\"zh\":\"中文\",\"mode\":\"素/営業/衝突/软肋\"}"})
        content = _request_once(cfg, msgs)
        if content:
            txt = re.sub(r"^```(json)?|```$", "", content, flags=re.M).strip()
            m = re.search(r"\{.*\}", txt, re.S)
            obj = json.loads(m.group(0) if m else txt)
            if obj.get("ja"):
                r = {"ja": obj.get("ja", ""), "zh": obj.get("zh", ""), "mode": obj.get("mode", "素")}
    except Exception as e:
        print("final reply failed:", type(e).__name__, str(e)[:120])

    if r is None:
        if final and not re.search(r"[{}]", final):
            r = {"ja": final[:120], "zh": "", "mode": "素"}
        else:
            r = dict(guard.FALLBACK) if guard.check(text)[0] else _pick("素")

    _history.append((text, r["ja"]))
    _save_memory()
    import threading
    threading.Thread(target=_compress_if_needed, daemon=True).start()
    return r
