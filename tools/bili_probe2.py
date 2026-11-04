"""探测收藏弹窗与评论框的选择器。"""
import pathlib, sys, time
sys.path.insert(0, str(pathlib.Path(r"E:\RentAGirl\tools")))
from bili_bot import Bili

b = Bili()
try:
    b.goto("https://www.bilibili.com/video/BV1GJ411x7h7", wait=4)
    # 点收藏
    b.page.click(".video-fav")
    time.sleep(2)
    btns = b.page.eval_on_selector_all(
        ".bili-dialog, .bili-dialog-bomb, .collect-popover, .van-popover",
        "els => els.map(e => ({cls: e.className, txt: (e.innerText||'').replace(/\\n/g,' | ').slice(0,160)}))")
    for x in btns[:5]:
        print("弹窗:", x, flush=True)
    # 找确认按钮
    for sel in [".bili-dialog .btn-confirm", ".bili-dialog button", ".collect-modal .btn-primary"]:
        print(sel, b.page.eval_on_selector_all(sel, "els => els.map(e => (e.innerText||'').trim().slice(0,10))"), flush=True)
    # 评论框
    b.page.evaluate("window.scrollBy(0, 1200)")
    time.sleep(2)
    for sel in [".reply-box .bili-rich-textarea__inner", "div[contenteditable='true']", ".reply-box-send"]:
        print(sel, b.page.eval_on_selector_all(sel, "els => els.length"), flush=True)
    txts = b.page.eval_on_selector_all("[contenteditable='true']",
        "els => els.map(e => ({cls: e.className.slice(0,60), ph: e.getAttribute('placeholder')||e.getAttribute('data-placeholder')||''}))")
    for x in txts[:5]:
        print("可编辑:", x, flush=True)
finally:
    b.close()
