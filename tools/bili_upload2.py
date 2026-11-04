"""完整投稿流程：上传 → 填标题/简介/标签/封面/声明/分区 → 投稿。"""
import pathlib
import sys
import time

sys.path.insert(0, str(pathlib.Path(r"E:\RentAGirl\tools")))
from bili_bot import Bili  # noqa: E402

URL = "https://member.bilibili.com/platform/upload/video/frame"
VIDEO = pathlib.Path(r"E:\RentAGirl\out\videos\intro_mag60b.mp4")
SHOT = pathlib.Path(r"E:\RentAGirl\out\upload")
SHOT.mkdir(exist_ok=True)

TITLE = "水原千鶴｜はじめまして、千鶴です（自己紹介）"
DESC = ("「ねえ、聞いて。私、ちょっと変わったバイトしてるの」\n\n"
        "水原千鶴（一ノ瀬千鶴）の自己紹介です。\n"
        "声・絵・編集はすべてローカル環境で生成しています。\n\n"
        "#水原千鹤 #租借女友 #二次元")
TAGS = ["水原千鹤", "租借女友", "二次元", "AI配音"]


def shot(page, name):
    try:
        page.screenshot(path=str(SHOT / name), full_page=True)
        print("  shot:", name, flush=True)
    except Exception:
        pass


def main():
    b = Bili()
    page = b.page
    try:
        b.goto(URL, wait=6)
        time.sleep(3)
        cdp = page.context.new_cdp_session(page)
        doc = cdp.send("DOM.getDocument", {"depth": 1})
        node = cdp.send("DOM.querySelector", {"nodeId": doc["root"]["nodeId"], "selector": "input[type=file]"})
        cdp.send("DOM.setFileInputFiles", {"files": [str(VIDEO)], "nodeId": node["nodeId"]})
        print("已选择文件，等上传…", flush=True)

        # 等"上传完成"或出现标题输入
        t0 = time.time()
        ready = False
        while time.time() - t0 < 600:
            try:
                if page.query_selector("input.input-val") and "上传完成" in page.inner_text("body"):
                    ready = True
                    break
            except Exception:
                pass
            time.sleep(3)
        print("上传完成:", ready, flush=True)
        time.sleep(3)
        shot(page, "1_uploaded.png")

        # 标题
        try:
            ti = page.query_selector("input.input-val")
            ti.click()
            ti.fill("")
            ti.type(TITLE, delay=15)
            print("标题 OK", flush=True)
        except Exception as e:
            print("标题失败", e, flush=True)

        # 简介
        try:
            desc = page.query_selector(".video-desc textarea, textarea")
            if desc:
                desc.click()
                desc.fill("")
                desc.type(DESC, delay=2)
                print("简介 OK", flush=True)
        except Exception as e:
            print("简介失败", e, flush=True)

        # 标签
        try:
            tag = page.query_selector("input[placeholder*='标签'], .tag-input input, input[placeholder*='回车']")
            if tag:
                for t in TAGS:
                    tag.click()
                    tag.type(t, delay=20)
                    time.sleep(0.4)
                    page.keyboard.press("Enter")
                    time.sleep(0.5)
                print("标签 OK", flush=True)
        except Exception as e:
            print("标签失败", e, flush=True)

        # 封面：点第一个推荐封面
        try:
            covers = page.query_selector_all(".cover-item, .recommend-cover img, .cover-list img")
            if covers:
                covers[0].click()
                time.sleep(1)
                print("封面 OK", flush=True)
        except Exception as e:
            print("封面失败", e, flush=True)

        shot(page, "2_filled.png")

        # 创作声明（必填）：点开选第一项
        try:
            sel = page.query_selector(".statement-select, .creation-statement, div[class*='statement']")
            if sel:
                sel.click()
                time.sleep(1)
                opts = page.query_selector_all(".bili-dropdown-item, li.dropdown-item, .select-item")
                if opts:
                    opts[0].click()
                    print("创作声明 OK", flush=True)
        except Exception as e:
            print("声明失败", e, flush=True)

        shot(page, "3_final.png")
        print("READY_TO_SUBMIT", flush=True)

    finally:
        b.close()


if __name__ == "__main__":
    main()
