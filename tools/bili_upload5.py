"""投稿 v5：干净的完整流程，封面用系统推荐图。"""
import pathlib
import sys
import time

sys.path.insert(0, str(pathlib.Path(r"E:\RentAGirl\tools")))
from bili_bot import Bili  # noqa: E402

URL = "https://member.bilibili.com/platform/upload/video/frame"
VIDEO = pathlib.Path(r"E:\RentAGirl\out\videos\intro_mag60b.mp4")
SHOT = pathlib.Path(r"E:\RentAGirl\out\upload")

TITLE = "水原千鶴｜はじめまして、千鶴です（自己紹介）"
DESC = ("「ねえ、聞いて。私、ちょっと変わったバイトしてるの」\n\n"
        "水原千鶴（一ノ瀬千鶴）の自己紹介です。\n"
        "声・絵・編集はすべてローカル環境で生成しています。\n\n"
        "#水原千鹤 #租借女友 #二次元")
TAGS = ["水原千鹤", "租借女友", "二次元"]
STATEMENT = "含AI生成内容"


def shot(page, name):
    try:
        page.screenshot(path=str(SHOT / name), full_page=True)
        print("  shot", name, flush=True)
    except Exception:
        pass


def main():
    b = Bili()
    page = b.page
    try:
        b.goto(URL, wait=8)
        time.sleep(4)
        cdp = page.context.new_cdp_session(page)
        doc = cdp.send("DOM.getDocument", {"depth": 1})
        node = cdp.send("DOM.querySelector", {"nodeId": doc["root"]["nodeId"], "selector": "input[type=file]"})
        cdp.send("DOM.setFileInputFiles", {"files": [str(VIDEO)], "nodeId": node["nodeId"]})
        print("上传中…", flush=True)

        t0 = time.time()
        while time.time() - t0 < 600:
            try:
                if "上传完成" in page.inner_text("body"):
                    break
            except Exception:
                pass
            time.sleep(3)
        print("上传完成", flush=True)
        time.sleep(4)
        shot(page, "v5_1.png")

        # 封面：点推荐封面的第一张
        try:
            ok = page.evaluate("""() => {
              const imgs = [...document.querySelectorAll('img')];
              const cand = imgs.filter(im => {
                const r = im.getBoundingClientRect();
                return r.width > 80 && r.width < 200 && r.height > 40 && r.top > 300;
              });
              if (cand.length) { cand[0].click(); return true; }
              return false;
            }""")
            print("封面点击:", ok, flush=True)
        except Exception as e:
            print("封面失败", e, flush=True)
        time.sleep(2)

        # 标题
        ti = page.query_selector("input.input-val")
        if ti:
            ti.click()
            ti.fill("")
            ti.type(TITLE, delay=10)
            print("标题 OK", flush=True)

        # 简介
        try:
            ta = page.get_by_placeholder("填写更全面的相关信息", exact=False)
            if ta.count():
                ta.first.click()
                ta.first.fill(DESC)
                print("简介 OK", flush=True)
        except Exception as e:
            print("简介失败", e, flush=True)

        # 标签
        try:
            tag = page.get_by_placeholder("按回车键Enter创建标签", exact=False)
            if tag.count():
                for t in TAGS:
                    tag.first.click()
                    tag.first.type(t, delay=10)
                    time.sleep(0.3)
                    page.keyboard.press("Enter")
                    time.sleep(0.4)
                print("标签 OK", flush=True)
        except Exception as e:
            print("标签失败", e, flush=True)

        # 创作声明
        try:
            page.locator("div[class*='select']").first.click()
            time.sleep(1)
            page.get_by_text(STATEMENT, exact=True).first.click()
            print("声明 OK", flush=True)
        except Exception as e:
            print("声明失败", e, flush=True)
        time.sleep(1)
        shot(page, "v5_2.png")

        # 投稿
        page.get_by_text("立即投稿", exact=True).first.click()
        print("已点投稿", flush=True)
        for i in range(12):
            time.sleep(3)
            txt = page.inner_text("body")
            if "投稿成功" in txt or "稿件投递成功" in txt or "等待审核" in txt:
                print("投稿成功提示出现", flush=True)
                break
        shot(page, "v5_3.png")
        txt = page.inner_text("body")
        print("URL:", page.url, flush=True)
        for kw in ("投稿成功", "审核", "上传失败", "请选择封面", "声明", "必填"):
            print(f"  包含 {kw}: {kw in txt}", flush=True)

    finally:
        b.close()


if __name__ == "__main__":
    main()
