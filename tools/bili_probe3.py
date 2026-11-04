"""打印收藏弹窗结构和评论"发布"按钮。"""
import pathlib, sys, time
sys.path.insert(0, str(pathlib.Path(r"E:\RentAGirl\tools")))
from bili_bot import Bili

b = Bili()
try:
    b.goto("https://www.bilibili.com/video/BV1GJ411x7h7", wait=4)
    b.page.click(".video-fav")
    time.sleep(2)
    html = b.page.eval_on_selector_all(".bili-dialog-bomb",
        "els => els.map(e => e.outerHTML.slice(0, 1200))")
    for h in html[:2]:
        print("DIALOG:", h.replace("\n", " ")[:1200], flush=True)

    b.page.evaluate("window.scrollBy(0, 1400)")
    time.sleep(2)
    btns = b.page.eval_on_selector_all("button, div[role='button'], span[class*='send']",
        "els => els.map(e => ({cls: (e.className||'').toString().slice(0,50), txt: (e.innerText||'').trim().slice(0,12)}))")
    interesting = [x for x in btns if x["txt"] in ("发布", "取消", "确定", "收藏", "发送")]
    print("按钮候选:", interesting[:10], flush=True)
finally:
    b.close()
