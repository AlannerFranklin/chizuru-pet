"""给已投稿的视频换自定义封面（编辑页 → 添加封面 → 上传图片 → 保存）。"""
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


def click_text(page, text):
    return page.evaluate("""(t) => {
      const els=[...document.querySelectorAll('div,span,button')].filter(e=>e.offsetParent!==null && e.textContent.trim()===t);
      if(!els.length) return 0;
      const el=els[els.length-1];
      ['mousedown','mouseup','click'].forEach(k=>el.dispatchEvent(new MouseEvent(k,{bubbles:true,cancelable:true})));
      return els.length;
    }""", text)


def main():
    b = Bili()
    page = b.page
    try:
        b.goto(EDIT, wait=8)
        page.bring_to_front()
        time.sleep(8)
        print("编辑页就绪:", bool(page.query_selector("input.input-val")), flush=True)

        # 鼠标移到封面区域，让"添加封面"出现，再点
        box = page.evaluate("""() => {
          const lab=[...document.querySelectorAll('div,span')].find(e=>e.offsetParent!==null && e.textContent.trim()==='封面');
          if(!lab) return null;
          const r=lab.getBoundingClientRect();
          return {x: r.x, y: r.y};
        }""")
        print("封面标签位置:", box, flush=True)
        if box:
            page.mouse.move(box["x"] + 130, box["y"] + 60)
            time.sleep(1)
        n = click_text(page, "添加封面")
        print("点添加封面:", n, flush=True)
        time.sleep(3)
        shot(page, "cover_dialog3.png")

        # 弹窗里的图片 input
        cdp = page.context.new_cdp_session(page)
        inputs = page.evaluate("""() => [...document.querySelectorAll('input[type=file]')].map((e,i)=>({i, accept:(e.accept||'').slice(0,60)}))""")
        print("inputs:", inputs, flush=True)
        idx = None
        for it in inputs:
            if ("jpg" in it["accept"]) or ("png" in it["accept"]) or ("image" in it["accept"]):
                idx = it["i"]
        print("图片输入索引:", idx, flush=True)
        if idx is not None:
            ok = False
            for _ in range(8):
                try:
                    doc = cdp.send("DOM.getDocument", {"depth": 1})
                    nodes = cdp.send("DOM.querySelectorAll", {"nodeId": doc["root"]["nodeId"], "selector": "input[type=file]"})
                    ids = nodes.get("nodeIds", [])
                    if len(ids) > idx:
                        cdp.send("DOM.setFileInputFiles", {"files": [str(COVER)], "nodeId": ids[idx]})
                        ok = True
                        break
                except Exception as e:
                    print("retry", type(e).__name__, flush=True)
                time.sleep(2)
            print("封面上传:", ok, flush=True)
        time.sleep(4)
        shot(page, "cover_uploaded.png")

        for t in ("完成", "确定", "确认", "保存"):
            if click_text(page, t):
                print("点了:", t, flush=True)
                break
        time.sleep(3)
        shot(page, "cover_after_confirm.png")

        # 保存修改
        n2 = click_text(page, "立即投稿")
        print("保存(立即投稿):", n2, flush=True)
        time.sleep(10)
        shot(page, "cover_saved.png")
        print("URL:", page.url, flush=True)

    finally:
        b.close()


if __name__ == "__main__":
    main()
