"""上传视频到 B 站（创作中心投稿页）。"""
import pathlib
import sys
import time

sys.path.insert(0, str(pathlib.Path(r"E:\RentAGirl\tools")))
from bili_bot import Bili  # noqa: E402

URL = "https://member.bilibili.com/platform/upload/video/frame"
VIDEO = pathlib.Path(r"E:\RentAGirl\out\videos\intro_mag60b.mp4")
SHOT = pathlib.Path(r"E:\RentAGirl\out\upload")
SHOT.mkdir(exist_ok=True)

TITLE = "水原千鶴｜はじめまして、千鶴です"
DESC = ("「ねえ、聞いて。私、ちょっと変わったバイトしてるの」\n\n"
        "水原千鶴（一ノ瀬千鶴）自己紹介。\n"
        "声・絵・編集はすべてローカルで生成しています。\n\n"
        "#水原千鹤 #租借女友 #AI配音")
TAGS = "水原千鹤,租借女友,二次元,AI配音,自我介绍"


def wait_for(page, fn, timeout=180, step=2):
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            v = fn()
            if v:
                return v
        except Exception:
            pass
        time.sleep(step)
    return None


def main():
    b = Bili()
    page = b.page
    try:
        b.goto(URL, wait=6)
        print("已打开投稿页:", page.url, flush=True)

        # 1) 选文件
        inputs = page.query_selector_all("input[type=file]")
        print("file inputs:", len(inputs), flush=True)
        if not inputs:
            print("找不到上传控件")
            return
        inputs[0].set_input_files(str(VIDEO))
        print("已提交文件，等待上传…", flush=True)

        # 2) 等上传完成（标题输入框出现即认为进入编辑页）
        def title_ready():
            return page.query_selector("input.input-val, .video-title input, input[placeholder*='标题']")

        el = wait_for(page, title_ready, timeout=420)
        page.screenshot(path=str(SHOT / "after_upload.png"))
        print("编辑页就绪:", bool(el), flush=True)
        if not el:
            print("上传可能超时，看截图")
            return

        time.sleep(3)
        # 3) 标题
        try:
            el.click()
            el.fill("")
            el.type(TITLE, delay=20)
            print("标题已填", flush=True)
        except Exception as e:
            print("填标题失败:", e, flush=True)

        # 4) 简介
        try:
            desc = page.query_selector("textarea, .desc-textarea, div[contenteditable='true']")
            if desc:
                desc.click()
                desc.type(DESC, delay=5)
                print("简介已填", flush=True)
        except Exception as e:
            print("填简介失败:", e, flush=True)

        # 5) 标签
        try:
            tag_in = page.query_selector("input[placeholder*='标签'], .tag-input input")
            if tag_in:
                for t in TAGS.split(","):
                    tag_in.click()
                    tag_in.type(t, delay=30)
                    page.keyboard.press("Enter")
                    time.sleep(0.6)
                print("标签已填", flush=True)
        except Exception as e:
            print("填标签失败:", e, flush=True)

        page.screenshot(path=str(SHOT / "before_submit.png"), full_page=True)
        print("已截图 before_submit.png", flush=True)
        print("TITLE_READY", flush=True)

    finally:
        b.close()


if __name__ == "__main__":
    main()
