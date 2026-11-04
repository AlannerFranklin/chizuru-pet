import json, pathlib, sys, urllib.request
sys.path.insert(0, r"E:\RentAGirl\pet")
import brain

cfg = json.loads(pathlib.Path(r"E:\RentAGirl\pet\config.json").read_text(encoding="utf-8"))
payload = {
    "model": cfg["model"],
    "messages": [{"role": "system", "content": brain._system_prompt()},
                 {"role": "user", "content": "今、疲れた…"}],
    "temperature": 0.8,
    "max_tokens": 300,
    "response_format": {"type": "json_object"},
}
body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
req = urllib.request.Request(cfg["base_url"].rstrip("/") + "/chat/completions",
                             data=body,
                             headers={"Content-Type": "application/json",
                                      "Authorization": "Bearer " + cfg["api_key"]})
with urllib.request.urlopen(req, timeout=60) as r:
    d = json.loads(r.read().decode("utf-8"))
print(json.dumps(d["choices"][0], ensure_ascii=False)[:1200])
