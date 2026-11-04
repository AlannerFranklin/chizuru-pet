"""投稿最终版：上传 → 填全字段 → 点立即投稿。"""
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
STATEMENT = "含AI生成内容"


def shot(page, name):
    try:
        page.screenshot(path=str(SHOT / name), full_page=True)
        print("  shot:", name, flush=True)
    except Exception:
        pass


def click_text(page, text, timeout=8):
    try:
        loc = page.get_by_text(text, exact=False).first
        loc.click(timeout=timeout * 1000)
        return True
    except Exception:
        return False


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
        print("已选文件，等上传…", flush=True)

        t0 = time.time()
        while time.time() - t0 < 600:
            try:
                if page.query_selector("input.input-val") and "上传完成" in page.inner_text("body"):
                    break
            except Exception:
                pass
            time.sleep(3)
        print("上传完成", flush=True)
        time.sleep(3)

        # 标题
        ti = page.query_selector("input.input-val")
        ti.click()
        ti.fill("")
        ti.type(TITLE, delay=12)
        print("标题 OK", flush=True)

        # 简介（找 placeholder 含"更全面"的 textarea）
        filled = False
        for ta in page.query_selector_all("textarea"):
            try:
                ph = ta.get_attribute("placeholder") or ""
                if "全面" in ph or "简介" in ph or ph == "":
                    ta.scroll_into_view_if_needed()
                    ta.click()
                    ta.fill(DESC)
                    filled = True
                    break
            except Exception:
                continue
        print("简介:", "OK" if filled else "未填", flush=True)

        # 标签
        try:
            tag = page.query_selector("input[placeholder*='标签'], .tag-input input, input[placeholder*='Enter']")
            if tag:
                for t in TAGS:
                    tag.click()
                    tag.type(t, delay=15)
                    time.sleep(0.3)
                    page.keyboard.press("Enter")
                    time.sleep(0.4)
                print("标签 OK", flush=True)
        except Exception as e:
            print("标签失败", e, flush=True)

        # 封面：点第一个推荐缩略图
        try:
            imgs = page.query_selector_all("img")
            picked = False
            for im in imgs:
                try:
                    box = im.bounding_box()
                    if box and 250 < box["y"] < 700 and box["width"] < 160 and box["height"] > 40:
                        im.click()
                        picked = True
                        break
                except Exception:
                    continue
            print("封面:", "OK" if picked else "跳过", flush=True)
        except Exception:
            pass
        time.sleep(1)

        # 创作声明
        try:
            sel = page.query_selector("div[class*='select'], .bcc-select")
            if sel:
                sel.click()
                time.sleep(1)
            if click_text(page, STATEMENT, 6):
                print("声明 OK:", STATEMENT, flush=True)
            else:
                print("声明：没找到选项", flush=True)
        except Exception as e:
            print("声明失败", e, flush=True)
        time.sleep(1)
        shot(page, "submit_filled.png")

        # 投稿
        ok = click_text(page, "立即投稿", 8)
        print("点击投稿:", ok, flush=True)
        time.sleep(6)
        shot(page, "after_submit.png")
        try:
            print("页面提示:", page.inner_text("body")[:300].replace("\n", " | "), flush=True)
        except Exception:
            pass

    finally:
        b.close()


if __name__ == "__main__":
    main()
