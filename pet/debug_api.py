import json, pathlib, urllib.request, urllib.error

cfg = json.loads(pathlib.Path(r"E:\RentAGirl\pet\config.json").read_text(encoding="utf-8"))
payload = {
    "model": cfg.get("model", "deepseek-chat"),
    "messages": [{"role": "user", "content": "用一句话说明你在"}],
    "max_tokens": 60,
    "response_format": {"type": "json_object"},
}
body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
req = urllib.request.Request(
    cfg["base_url"].rstrip("/") + "/chat/completions",
    data=body,
    headers={"Content-Type": "application/json",
             "Authorization": "Bearer " + cfg["api_key"]},
)
try:
    with urllib.request.urlopen(req, timeout=40) as r:
        raw = r.read()
        print("status", r.status, "bytes", len(raw))
        print(raw[:400].decode("utf-8", "replace"))
except urllib.error.HTTPError as e:
    print("HTTP", e.code)
    print(e.read()[:500].decode("utf-8", "replace"))
except Exception as e:
    print("ERR", type(e).__name__, e)
