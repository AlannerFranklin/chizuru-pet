"""探查投稿页 iframe 结构。"""
import pathlib
import sys
import time

sys.path.insert(0, str(pathlib.Path(r"E:\RentAGirl\tools")))
from bili_bot import Bili  # noqa: E402

URL = "https://member.bilibili.com/platform/upload/video/frame"

b = Bili()
try:
    b.goto(URL, wait=8)
    time.sleep(3)
    print("frames:", [(f.name, f.url) for f in b.page.frames], flush=True)
    for f in b.page.frames:
        try:
            n_file = f.eval_on_selector_all("input[type=file]", "els => els.length")
            n_txt = f.eval_on_selector_all("input, textarea", "els => els.length")
            print(f"  frame {f.name or f.url[:50]} file={n_file} inputs={n_txt}", flush=True)
        except Exception as e:
            print("  frame err", type(e).__name__, flush=True)
    # 主页面 body 文本片段
    try:
        txt = b.page.inner_text("body")[:400].replace("\n", " | ")
        print("body:", txt, flush=True)
    except Exception:
        pass
finally:
    b.close()
