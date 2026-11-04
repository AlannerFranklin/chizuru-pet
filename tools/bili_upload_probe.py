"""探查 B 站投稿页结构：找上传 input、标题框、按钮。"""
import pathlib
import sys
import time

sys.path.insert(0, str(pathlib.Path(r"E:\RentAGirl\tools")))
from bili_bot import Bili  # noqa: E402

URL = "https://member.bilibili.com/platform/upload/video/frame"

b = Bili()
try:
    print("logged in:", b.logged_in(), flush=True)
    b.goto(URL, wait=6)
    print("url:", b.page.url, flush=True)
    print("title:", b.page.title(), flush=True)
    time.sleep(3)
    for sel in ["input[type=file]", ".upload-btn", ".bcc-upload", "input.bili-upload-input",
                ".video-title input", "input[placeholder]", "textarea"]:
        n = b.page.eval_on_selector_all(sel, "els => els.map(e => ({tag:e.tagName, cls:(e.className||'').toString().slice(0,40), ph:e.placeholder||'', type:e.type||''}))")
        print(f"{sel}: {n[:3]}", flush=True)
    b.page.screenshot(path=r"E:\RentAGirl\out\upload_page.png")
    print("screenshot saved")
finally:
    b.close()
