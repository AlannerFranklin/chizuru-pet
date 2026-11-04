"""子代理：给她派一个独立的小任务，子代理自己用工具做完再回报。
只能用心 工作区 + 联网 的工具，不能再派子代理（防递归）。
"""
import json
import re
import sys

sys.path.insert(0, r"E:\RentAGirl\pet")

SUB_TOOLS = ["list_dir", "read_file", "write_file", "run_cmd", "run_python",
             "web_search", "web_fetch"]

SYS = """你是水原千鹤的助手，负责独立完成她交代的子任务。
你有工具：列目录、读写文件、跑 PowerShell、跑 Python、联网搜索、抓网页。
直接动手做完，最后用一两句话汇报结果（中文）。不要问问题，不要描述过程。"""


def run_task(task, max_steps=8):
    import brain
    import actions

    cfg = brain._load_config()
    if not cfg:
        return "没有可用的模型配置"
    tools = [t for t in actions.TOOLS if t["function"]["name"] in SUB_TOOLS]
    msgs = [{"role": "system", "content": SYS},
            {"role": "user", "content": task}]
    notes = []
    for _ in range(max_steps):
        try:
            msg = brain._request_tools(cfg, msgs, tools)
        except Exception as e:
            return f"子代理调用失败：{type(e).__name__} {e}"
        calls = msg.get("tool_calls") or []
        if calls:
            msgs.append({"role": "assistant", "content": msg.get("content") or "", "tool_calls": calls})
            for c in calls:
                name = c["function"]["name"]
                try:
                    args = json.loads(c["function"].get("arguments") or "{}")
                except Exception:
                    args = {}
                res = actions.call(name, args)
                notes.append(f"{name} -> {str(res)[:100]}")
                msgs.append({"role": "tool", "tool_call_id": c["id"], "content": str(res)})
            continue
        final = (msg.get("content") or "").strip()
        if final:
            return final[:1500]
        break
    return ("子代理没给出结论。做过的事：\n" + "\n".join(notes[-6:])).strip()
