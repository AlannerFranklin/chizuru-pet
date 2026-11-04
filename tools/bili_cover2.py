"""换封面：打开封面设置 → CDP 上传图片 → 完成 → 保存修改。"""
import pathlib
import sys
import time

sys.path.insert(0, str(pathlib.Path(r"E:\RentAGirl\tools")))
from bili_bot import Bili  # noqa: E402

EDIT = "https://member.bilibili.com/platform/upload/video/frame?type=edit&bvid=BV1GJx167Ep9"
COVER = pathlib.Path(r"E:\RentAGirl\out\cover\cover_v1.jpg")
SHOT = pathlib.Path(r"E:\RentAGirl\out\upload")


def shot(page, n):
    try:
        page.screenshot(path=str(SHOT / n), full_page=True)
        print("  shot", n, flush=True)
    except Exception:
        pass


def click_text(page, t):
    return page.evaluate("""(t) => {
      const els=[...document.querySelectorAll('div,span,button')].filter(e=>e.offsetParent!==null && e.textContent.trim()===t);
      if(!els.length) return 0;
      const el=els[els.length-1];
      el.scrollIntoView({block:'center'});
      ['mousedown','mouseup','click'].forEach(k=>el.dispatchEvent(new MouseEvent(k,{bubbles:true,cancelable:true})));
      return els.length;
    }""", t)


def main():
    b = Bili()
    page = b.page
    try:
        b.goto(EDIT, wait=8)
        page.bring_to_front()
        time.sleep(8)
        page.locator(".cover-slot").first.click(force=True)
        time.sleep(3)
        print("封面弹窗已开", flush=True)

        cdp = page.context.new_cdp_session(page)
        done = False
        for _ in range(10):
            try:
                doc = cdp.send("DOM.getDocument", {"depth": 1})
                nodes = cdp.send("DOM.querySelectorAll", {"nodeId": doc["root"]["nodeId"],
                                                          "selector": "input[type=file][accept*='image']"})
                ids = nodes.get("nodeIds", [])
                if ids:
                    cdp.send("DOM.setFileInputFiles", {"files": [str(COVER)], "nodeId": ids[0]})
                    done = True
                    break
            except Exception as e:
                print("retry", type(e).__name__, flush=True)
            time.sleep(2)
        print("封面上传:", done, flush=True)
        time.sleep(5)
        shot(page, "cv_uploaded.png")

        click_text(page, "完成")
        print("点完成", flush=True)
        time.sleep(4)
        shot(page, "cv_done.png")

        # 保存
        for label in ("立即投稿", "保存", "提交", "发布"):
            if click_text(page, label):
                print("保存按钮:", label, flush=True)
                break
        time.sleep(10)
        shot(page, "cv_saved.png")
        print("URL:", page.url, flush=True)
        txt = page.inner_text("body")
        print("含成功:", any(k in txt for k in ("保存成功", "更新成功", "投递成功", "审核")), flush=True)

    finally:
        b.close()


if __name__ == "__main__":
    main()
