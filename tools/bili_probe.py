"""在一个视频页上，找点赞/收藏/评论的按钮选择器。"""
import pathlib, sys, time, json
sys.path.insert(0, str(pathlib.Path(r"E:\RentAGirl\tools")))
from bili_bot import Bili

b = Bili()
try:
    b.goto("https://www.bilibili.com/video/BV1GJ411x7h7", wait=4)
    info = b.video_info()
    print("title:", info["title"], flush=True)
    # 工具栏按钮
    items = b.page.eval_on_selector_all(
        ".video-toolbar-left-item, .toolbar-left-item, .video-like, .video-fav, .video-share",
        """els => els.map(e => ({
            cls: e.className,
            txt: (e.innerText||'').trim().slice(0,20),
            title: e.getAttribute('title')||''
        }))""")
    for it in items[:12]:
        print(it, flush=True)
    # 收藏按钮的常见类名
    for sel in [".video-fav", ".toolbar-left-item-wrap:nth-child(2)", ".video-toolbar-left-item"]:
        n = b.page.eval_on_selector_all(sel, "els => els.length")
        print(sel, "count", n, flush=True)
finally:
    b.close()
