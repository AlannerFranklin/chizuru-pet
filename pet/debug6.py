import json, pathlib, sys, urllib.request
sys.path.insert(0, r"E:\RentAGirl\pet")
import brain

cfg = json.loads(pathlib.Path(r"E:\RentAGirl\pet\config.json").read_text(encoding="utf-8"))
for q in ["何か可愛いこと言ってよ", "今日ほんと可愛いね"]:
    msgs = [{"role": "system", "content": brain._system_prompt()},
            {"role": "user", "content": q}]
    body = json.dumps({"model": cfg["model"], "messages": msgs, "temperature": 0.8,
                       "max_tokens": 300, "response_format": {"type": "json_object"}},
                      ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(cfg["base_url"].rstrip("/") + "/chat/completions",
                                 data=body,
                                 headers={"Content-Type": "application/json",
                                          "Authorization": "Bearer " + cfg["api_key"]})
    with urllib.request.urlopen(req, timeout=60) as r:
        d = json.loads(r.read().decode("utf-8"))
    ch = d["choices"][0]
    print("Q:", q)
    print("  finish:", ch.get("finish_reason"), "usage:", d.get("usage", {}).get("completion_tokens"))
    print("  message keys:", list(ch["message"].keys()))
    print("  content len:", len(ch["message"].get("content") or ""))
    rc = ch["message"].get("reasoning_content")
    if rc:
        print("  reasoning:", repr(rc)[:200])
