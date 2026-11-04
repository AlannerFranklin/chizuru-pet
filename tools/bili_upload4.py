"""投稿（最终版 v4）：上传 → 自定义封面(CDP) → 标题/简介/标签/声明 → 投稿。"""
import pathlib
import sys
import time

from PIL import Image

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


def make_cover():
    """从视频抽一帧做封面（16:9，1146x717 推荐比例）。"""
    import subprocess
    out = SHOT / "cover.jpg"
    if out.exists():
        return out
    subprocess.run([r"E:\RentAGirl\bin\ffmpeg.exe", "-y", "-ss", "6", "-i", str(VIDEO),
                    "-frames:v", "1", "-q:v", "2", str(out)],
                   capture_output=True, creationflags=0x08000000)
    im = Image.open(out).convert("RGB").resize((1146, 645), Image.LANCZOS)
    im.save(out, quality=95)
    return out


def set_file_in_page(page, files, index=0):
    cdp = page.context.new_cdp_session(page)
    doc = cdp.send("DOM.getDocument", {"depth": -1})
    nodes = cdp.send("DOM.querySelectorAll", {"nodeId": doc["root"]["nodeId"], "selector": "input[type=file]"})
    ids = nodes.get("nodeIds", [])
    if len(ids) <= index:
        return False
    cdp.send("DOM.setFileInputFiles", {"files": files, "nodeId": ids[index]})
    return True


def main():
    cover = make_cover()
    b = Bili()
    page = b.page
    try:
        b.goto(URL, wait=6)
        time.sleep(3)
        set_file_in_page(page, [str(VIDEO)], 0)
        print("已选视频，等上传…", flush=True)

        t0 = time.time()
        while time.time() - t0 < 600:
            try:
                if "上传完成" in page.inner_text("body"):
                    break
            except Exception:
                pass
            time.sleep(3)
        print("上传完成", flush=True)
        time.sleep(3)

        # 标题
        ti = page.query_selector("input.input-val")
        if ti:
            ti.click()
            ti.fill("")
            ti.type(TITLE, delay=10)
            print("标题 OK", flush=True)

        # 简介
        try:
            tas = page.query_selector_all("textarea")
            for ta in tas:
                ta.scroll_into_view_if_needed()
                ta.click()
                ta.fill(DESC)
                print("简介 OK", flush=True)
                break
        except Exception as e:
            print("简介失败", e, flush=True)

        # 标签
        try:
            tag = page.query_selector("input[placeholder*='标签'], input[placeholder*='回车']")
            if tag:
                for t in TAGS:
                    tag.click()
                    tag.type(t, delay=12)
                    time.sleep(0.3)
                    page.keyboard.press("Enter")
                    time.sleep(0.4)
                print("标签 OK", flush=True)
        except Exception as e:
            print("标签失败", e, flush=True)

        # 封面：点"添加封面"→ 弹窗里上传自定义图
        try:
            if page.get_by_text("添加封面").count():
                page.get_by_text("添加封面").first.click()
                time.sleep(2)
                if set_file_in_page(page, [str(cover)], 0):
                    time.sleep(3)
                    shot(page, "cover_dialog.png")
                    # 弹窗确认按钮
                    for txt in ("确认", "完成", "确定", "上传"):
                        try:
                            btn = page.get_by_text(txt, exact=True)
                            if btn.count():
                                btn.first.click()
                                break
                        except Exception:
                            continue
                    time.sleep(2)
                    print("封面 OK", flush=True)
        except Exception as e:
            print("封面失败", e, flush=True)

        # 创作声明
        try:
            page.locator("div[class*='select']").first.click()
            time.sleep(1)
            opt = page.get_by_text(STATEMENT, exact=False)
            if opt.count():
                opt.first.click()
                print("声明 OK", flush=True)
            else:
                page.keyboard.press("ArrowDown")
                page.keyboard.press("Enter")
                print("声明(键盘) OK", flush=True)
        except Exception as e:
            print("声明失败", e, flush=True)

        time.sleep(1)
        shot(page, "v4_before_submit.png")

        # 投稿
        try:
            page.get_by_text("立即投稿").first.click()
            print("已点投稿", flush=True)
        except Exception as e:
            print("点投稿失败", e, flush=True)
        time.sleep(8)
        shot(page, "v4_after_submit.png")
        txt = page.inner_text("body")
        for kw in ("投稿成功", "审核", "请完成", "必填", "封面", "声明"):
            if kw in txt:
                print("页面含关键词:", kw, flush=True)

    finally:
        b.close()


if __name__ == "__main__":
    main()
