import json, pathlib, sys, urllib.request, urllib.error
sys.path.insert(0, r"E:\RentAGirl\pet")
import brain

cfg = json.loads(pathlib.Path(r"E:\RentAGirl\pet\config.json").read_text(encoding="utf-8"))
sp = brain._system_prompt()
print("system prompt chars:", len(sp))
print("contains json:", "json" in sp.lower())

payload = {
    "model": cfg["model"],
    "messages": [{"role": "system", "content": sp},
                 {"role": "user", "content": "ねえ、俺のこと好き?"}],
    "temperature": 0.8,
    "max_tokens": 300,
    "response_format": {"type": "json_object"},
}
body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
req = urllib.request.Request(cfg["base_url"].rstrip("/") + "/chat/completions",
                             data=body,
                             headers={"Content-Type": "application/json",
                                      "Authorization": "Bearer " + cfg["api_key"]})
try:
    with urllib.request.urlopen(req, timeout=60) as r:
        raw = r.read()
        d = json.loads(raw.decode("utf-8"))
        print("finish:", d["choices"][0].get("finish_reason"))
        print("content:", repr(d["choices"][0]["message"]["content"])[:600])
except urllib.error.HTTPError as e:
    print("HTTP", e.code, e.read()[:400].decode("utf-8", "replace"))
except Exception as e:
    print("ERR", type(e).__name__, e)
