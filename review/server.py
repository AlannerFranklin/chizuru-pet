"""人工审核千鹤语音的小服务：浏览 1937 段，逐句标记「好 / 有问题 / 跳过」。
启动: python server.py  → 浏览器打开 http://127.0.0.1:8765
"""
import json
import pathlib
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ROOT = pathlib.Path(__file__).resolve().parent
INDEX = json.loads((ROOT / "index.json").read_text(encoding="utf-8"))
BY_ID = {it["id"]: it for it in INDEX}
VOTES = ROOT / "votes.jsonl"
PORT = 8765


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, code, body, ctype="application/json; charset=utf-8"):
        if isinstance(body, str):
            body = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urllib.parse.urlparse(self.path).path
        if path in ("/", "/index.html"):
            return self._send(200, (ROOT / "index.html").read_bytes(), "text/html; charset=utf-8")
        if path == "/api/index":
            return self._send(200, json.dumps(INDEX, ensure_ascii=False))
        if path == "/api/stats":
            counts = {}
            if VOTES.exists():
                for line in VOTES.open(encoding="utf-8"):
                    try:
                        v = json.loads(line)
                        counts[v["vote"]] = counts.get(v["vote"], 0) + 1
                    except Exception:
                        pass
            return self._send(200, json.dumps(counts))
        if path.startswith("/audio/"):
            cid = urllib.parse.unquote(path[len("/audio/"):])
            it = BY_ID.get(cid)
            if not it:
                return self._send(404, "{}")
            p = pathlib.Path(it["file"])
            if not p.exists():
                return self._send(404, "{}")
            data = p.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "audio/wav")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return
        return self._send(404, "{}")

    def do_POST(self):
        if urllib.parse.urlparse(self.path).path != "/api/vote":
            return self._send(404, "{}")
        n = int(self.headers.get("Content-Length", 0))
        try:
            data = json.loads(self.rfile.read(n).decode("utf-8"))
        except Exception:
            return self._send(400, "{}")
        with VOTES.open("a", encoding="utf-8") as f:
            f.write(json.dumps(data, ensure_ascii=False) + "\n")
        return self._send(200, json.dumps({"ok": True}))


if __name__ == "__main__":
    print(f"http://127.0.0.1:{PORT}  ({len(INDEX)} clips)")
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
