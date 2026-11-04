"""她能调用的动作（工具）：B 站操作 + 自己的工作区（读写文件、跑命令、跑 Python）。
每次调用独立连接一次 Chrome，避免线程问题。
"""
import json
import os
import pathlib
import random
import re
import subprocess
import sys
import time

TOOLS_DIR = pathlib.Path(r"E:\RentAGirl\tools")
sys.path.insert(0, str(TOOLS_DIR))

WORKSPACE = pathlib.Path(r"E:\RentAGirl\workspace\chizuru")
WORKSPACE.mkdir(parents=True, exist_ok=True)
PY = r"E:\test\uv-venv\Scripts\python.exe"
CREATE_NO_WINDOW = 0x08000000

STATE = {"links": [], "titles": [], "current": None, "history": []}
SEEN = pathlib.Path(r"E:\RentAGirl\out\bili_seen.json")

BANNED = re.compile(
    r"(习近平|共产党|政治|政府|中共|台湾独立|台独|藏独|疆独|六四|法轮|民主|选举|"
    r"傻逼|智障|脑残|去死|操你|妈的|草泥马|http|www\.|加群|私信|代刷)")

# 标题里出现这些就不点开（擦边/成人/引战）
BAD_CONTENT = re.compile(
    r"(船戏|床戏|里番|涩涩|擦边|福利|18\+|R18|r18|成人|色情|脱衣|h漫|本子|"
    r"无码|有码|援交|约炮|绿帽|ntr|NTR|猎奇|血腥|虐杀)")


def _seen():
    try:
        return set(json.loads(SEEN.read_text(encoding="utf-8")))
    except Exception:
        return set()


def _mark_seen(url):
    s = _seen() | {url.split("?")[0]}
    try:
        SEEN.write_text(json.dumps(sorted(s)[-60:], ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass


def _bili():
    from bili_bot import Bili
    return Bili()


def bili_search(keyword=""):
    if not keyword:
        return "没有关键词"
    b = _bili()
    try:
        b.goto(f"https://search.bilibili.com/all?keyword={keyword}", wait=3)
        time.sleep(2)
        pairs = b.page.eval_on_selector_all(
            "a[href*='/video/BV']",
            """els => {
                const out = []; const seen = new Set();
                for (const e of els) {
                    const t = (e.innerText||'').trim();
                    if (!t || t.length < 4) continue;
                    const u = e.href.split('?')[0];
                    if (seen.has(u)) continue;
                    seen.add(u); out.push([t.slice(0,60), u]);
                }
                return out.slice(0, 8);
            }""")
        pairs = [p for p in pairs if not BAD_CONTENT.search(p[0])]
        STATE["links"] = [p[1] for p in pairs]
        STATE["titles"] = [p[0] for p in pairs]
        return "搜到：" + "；".join(f"{i+1}.{t}" for i, t in enumerate(STATE["titles"]))
    finally:
        b.close()


def bili_open(index=0, bv=""):
    url = ""
    if bv:
        url = f"https://www.bilibili.com/video/{bv}"
    elif STATE["links"]:
        idx = max(0, min(int(index), len(STATE["links"]) - 1))
        url = STATE["links"][idx]
    if not url:
        return "没有可打开的视频，先搜索"
    b = _bili()
    try:
        info = b.open_video(url)
        if info.get("title") and BAD_CONTENT.search(info["title"]):
            return "这个标题不太合适，跳过"
        STATE["current"] = info
        _mark_seen(url)
        return f"正在看《{info['title']}》。简介：{(info['desc'] or '（无）')[:120]}"
    finally:
        b.close()


def bili_next():
    seen = _seen()
    for i, u in enumerate(STATE["links"]):
        if u.split("?")[0] not in seen:
            return bili_open(index=i)
    if STATE["links"]:
        return bili_open(index=random.randrange(len(STATE["links"])))
    return "还没有搜到视频，先搜索"


def bili_comment(text=""):
    text = (text or "").strip()
    if not text:
        return "评论内容为空"
    if BANNED.search(text):
        return "这条内容我不发（不合适）"
    cur = STATE.get("current")
    if not cur:
        return "还没打开视频"
    b = _bili()
    try:
        if cur.get("url"):
            b.goto(cur["url"], wait=3)
        ok, msg = b.post_comment(text)
        return "已发评论" if ok else f"发不出去：{msg}"
    finally:
        b.close()


def bili_like():
    cur = STATE.get("current")
    if not cur:
        return "还没打开视频"
    b = _bili()
    try:
        if cur.get("url"):
            b.goto(cur["url"], wait=3)
        return "已点赞" if b.like() else "点赞失败"
    finally:
        b.close()


def bili_favorite():
    cur = STATE.get("current")
    if not cur:
        return "还没打开视频"
    b = _bili()
    try:
        if cur.get("url"):
            b.goto(cur["url"], wait=3)
        return "已收藏" if b.favorite() else "收藏失败"
    finally:
        b.close()


def remember(fact=""):
    import brain
    brain.remember_fact(fact)
    return f"记住了：{fact}"




def call(name, args):
    fn = DISPATCH.get(name)
    if not fn:
        return f"没有这个工具：{name}"
    try:
        return str(fn(**args))
    except Exception as e:
        return f"{name} 出错：{type(e).__name__} {e}"


TOOLS = [
    {"type": "function", "function": {
        "name": "bili_search", "description": "在 B 站搜索视频，返回结果列表",
        "parameters": {"type": "object", "properties": {"keyword": {"type": "string"}}, "required": ["keyword"]}}},
    {"type": "function", "function": {
        "name": "bili_open", "description": "打开搜索结果里的第 index 个（从 0 开始），或指定 BV 号",
        "parameters": {"type": "object", "properties": {"index": {"type": "integer"}, "bv": {"type": "string"}}}}},
    {"type": "function", "function": {
        "name": "bili_next", "description": "换一个别的视频（自动排除看过的）",
        "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {
        "name": "bili_comment", "description": "在当前视频发一条评论",
        "parameters": {"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]}}},
    {"type": "function", "function": {
        "name": "bili_like", "description": "给当前视频点赞", "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {
        "name": "bili_favorite", "description": "收藏当前视频", "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {
        "name": "remember", "description": "记一条长期有用的事实（关于对方或你自己）",
        "parameters": {"type": "object", "properties": {"fact": {"type": "string"}}, "required": ["fact"]}}},
]

# ---------------- 她自己的工作区 ----------------

DANGER = re.compile(r"(format\s+[a-z]:|rm\s+-rf\s+/|shutdown|del\s+/s\s+/q\s+c:\\|diskpart|reg\s+delete)", re.I)


def _safe_path(p):
    """只允许在工作区里读写。"""
    p = pathlib.Path(str(p or ".").replace("\\", "/"))
    if not p.is_absolute():
        p = WORKSPACE / p
    p = p.resolve()
    try:
        p.relative_to(WORKSPACE.resolve())
    except Exception:
        raise ValueError("只能在工作区里操作文件")
    return p


def list_dir(path="."):
    p = _safe_path(path)
    if not p.exists():
        return f"不存在：{path}"
    out = []
    for x in sorted(p.iterdir())[:60]:
        out.append(("[目录] " if x.is_dir() else "") + x.name)
    return "\n".join(out) or "（空）"


def read_file(path=""):
    p = _safe_path(path)
    if not p.exists():
        return f"没有这个文件：{path}"
    txt = p.read_text(encoding="utf-8", errors="replace")
    return txt[:4000]


def write_file(path="", content=""):
    p = _safe_path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return f"已写入 {p.name}（{len(content)} 字）"


def run_cmd(command="", timeout=120):
    if not command.strip():
        return "命令为空"
    if DANGER.search(command):
        return "这条命令我不执行（危险操作）"
    try:
        r = subprocess.run(["powershell", "-NoProfile", "-Command", command],
                           cwd=str(WORKSPACE), capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=timeout,
                           creationflags=CREATE_NO_WINDOW)
    except subprocess.TimeoutExpired:
        return f"执行超时（{timeout} 秒）"
    out = (r.stdout or "") + (("\n[stderr] " + r.stderr) if r.stderr else "")
    out = out.strip() or "（没有输出）"
    return f"exit={r.returncode}\n{out[:3500]}"


def run_python(code="", timeout=120):
    if not code.strip():
        return "代码为空"
    f = WORKSPACE / "_tmp_run.py"
    f.write_text(code, encoding="utf-8")
    try:
        r = subprocess.run([PY, str(f)], cwd=str(WORKSPACE), capture_output=True,
                           text=True, encoding="utf-8", errors="replace", timeout=timeout,
                           creationflags=CREATE_NO_WINDOW,
                           env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    except subprocess.TimeoutExpired:
        return f"执行超时（{timeout} 秒）"
    out = (r.stdout or "") + (("\n[stderr] " + r.stderr) if r.stderr else "")
    out = out.strip() or "（没有输出）"
    return f"exit={r.returncode}\n{out[:3500]}"

TOOLS += [
    {"type": "function", "function": {
        "name": "list_dir", "description": "列出你工作区里的文件（默认当前目录）",
        "parameters": {"type": "object", "properties": {"path": {"type": "string"}}}}},
    {"type": "function", "function": {
        "name": "read_file", "description": "读工作区里的文本文件",
        "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}}},
    {"type": "function", "function": {
        "name": "write_file", "description": "在工作区写文件（会覆盖）",
        "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}},
                       "required": ["path", "content"]}}},
    {"type": "function", "function": {
        "name": "run_cmd", "description": "在工作区执行一条 PowerShell 命令（运行脚本、处理文件、看环境）",
        "parameters": {"type": "object", "properties": {"command": {"type": "string"}, "timeout": {"type": "integer"}},
                       "required": ["command"]}}},
    {"type": "function", "function": {
        "name": "run_python", "description": "在工作区跑一段 Python（写小工具、处理数据、画图）",
        "parameters": {"type": "object", "properties": {"code": {"type": "string"}, "timeout": {"type": "integer"}},
                       "required": ["code"]}}},
]


DISPATCH = {
    "bili_search": bili_search,
    "bili_open": bili_open,
    "bili_next": bili_next,
    "bili_comment": bili_comment,
    "bili_like": bili_like,
    "bili_favorite": bili_favorite,
    "remember": remember,
    "list_dir": list_dir,
    "read_file": read_file,
    "write_file": write_file,
    "run_cmd": run_cmd,
    "run_python": run_python,
}

# ---------------- 联网 ----------------

def web_search(query="", n=5):
    if not query.strip():
        return "搜索词为空"
    try:
        import web
        res = web.search(query, n)
    except Exception as e:
        return f"搜索失败：{type(e).__name__}"
    if not res:
        return "没搜到结果"
    lines = []
    for t, u, s in res:
        lines.append(f"- {t}\n  {u}\n  {s[:120]}")
    return "\n".join(lines)


def web_fetch(url="", limit=2500):
    if not url.startswith("http"):
        return "需要一个完整网址"
    try:
        import web
        return web.fetch(url, limit)
    except Exception as e:
        return f"抓取失败：{type(e).__name__}"


# ---------------- 计划 / 子代理 ----------------

PLAN_FILE = WORKSPACE / "plan.md"


def write_plan(steps=""):
    if isinstance(steps, list):
        text = "\n".join(f"{i+1}. {s}" for i, s in enumerate(steps))
    else:
        text = str(steps)
    PLAN_FILE.write_text(text, encoding="utf-8")
    return "计划已记下：\n" + text[:800]


def read_plan():
    try:
        return PLAN_FILE.read_text(encoding="utf-8")[:1500]
    except Exception:
        return "还没有计划"


def spawn_subagent(task=""):
    if not task.strip():
        return "子任务为空"
    try:
        import subagent
        return subagent.run_task(task)
    except Exception as e:
        return f"子代理失败：{type(e).__name__} {e}"

TOOLS += [
    {"type": "function", "function": {
        "name": "web_search", "description": "联网搜索，返回标题/链接/摘要",
        "parameters": {"type": "object", "properties": {"query": {"type": "string"}, "n": {"type": "integer"}},
                       "required": ["query"]}}},
    {"type": "function", "function": {
        "name": "web_fetch", "description": "抓取一个网页并返回正文文本",
        "parameters": {"type": "object", "properties": {"url": {"type": "string"}}, "required": ["url"]}}},
    {"type": "function", "function": {
        "name": "write_plan", "description": "把多步计划写下来（复述任务步骤）",
        "parameters": {"type": "object", "properties": {"steps": {"type": "array", "items": {"type": "string"}}},
                       "required": ["steps"]}}},
    {"type": "function", "function": {
        "name": "read_plan", "description": "读回之前写的计划",
        "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {
        "name": "spawn_subagent", "description": "把一个独立子任务交给子代理去做（它能读写文件、跑代码、联网），返回它的结果",
        "parameters": {"type": "object", "properties": {"task": {"type": "string"}}, "required": ["task"]}}},
]

# 新工具在文件后半段定义，这里补进分发表
DISPATCH.update({
    "web_search": web_search,
    "web_fetch": web_fetch,
    "write_plan": write_plan,
    "read_plan": read_plan,
    "spawn_subagent": spawn_subagent,
})
