"""投稿 v7：bring_to_front + 可见元素点击 + Quill 编辑器输入。"""
import pathlib
import sys
import time

sys.path.insert(0, str(pathlib.Path(r"E:\RentAGirl\tools")))
from bili_bot import Bili  # noqa: E402

URL = "https://member.bilibili.com/platform/upload/video/frame"
VIDEO = pathlib.Path(r"E:\RentAGirl\out\videos\intro_mag60b.mp4")
SHOT = pathlib.Path(r"E:\RentAGirl\out\upload")

TITLE = "水原千鶴｜はじめまして、千鶴です（自己紹介）"
DESC = "「ねえ、聞いて。私、ちょっと変わったバイトしてるの」 水原千鶴（一ノ瀬千鶴）の自己紹介です。声・絵・編集はすべてローカル環境で生成しています。"
TAGS = ["水原千鹤", "租借女友", "二次元"]
STATEMENT = "含AI生成内容"

CLICK_JS = """(t) => {
  const els=[...document.querySelectorAll('div,span,button,li')]
    .filter(e=>e.textContent.trim()===t && e.offsetParent!==null);
  if(!els.length) return 0;
  const el = els[els.length-1];
  el.scrollIntoView({block:'center'});
  ['mousedown','mouseup','click'].forEach(k=>el.dispatchEvent(new MouseEvent(k,{bubbles:true,cancelable:true})));
  return els.length;
}"""


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
        page.bring_to_front()
        time.sleep(4)
        cdp = page.context.new_cdp_session(page)
        attached = False
        for attempt in range(12):
            try:
                doc = cdp.send("DOM.getDocument", {"depth": 1})
                node = cdp.send("DOM.querySelector", {"nodeId": doc["root"]["nodeId"], "selector": "input[type=file]"})
                if node.get("nodeId"):
                    cdp.send("DOM.setFileInputFiles", {"files": [str(VIDEO)], "nodeId": node["nodeId"]})
                    attached = True
                    break
            except Exception as e:
                print("attach retry", attempt, type(e).__name__, flush=True)
            time.sleep(2)
        print("文件已附加:", attached, flush=True)
        print("上传中…", flush=True)
        t0 = time.time()
        while time.time() - t0 < 600:
            if "上传完成" in page.inner_text("body"):
                break
            time.sleep(3)
        page.bring_to_front()
        time.sleep(6)
        print("上传完成", flush=True)

        # 标题
        try:
            ti = page.query_selector("input.input-val")
            ti.click()
            ti.fill("")
            ti.type(TITLE, delay=8)
            print("标题 OK", flush=True)
        except Exception as e:
            print("标题失败", e, flush=True)

        # 简介（Quill）
        try:
            ed = page.query_selector(".ql-editor")
            if ed:
                ed.click()
                page.keyboard.type(DESC, delay=1)
                print("简介 OK", flush=True)
        except Exception as e:
            print("简介失败", e, flush=True)

        # 标签
        try:
            tag = page.get_by_placeholder("按回车键Enter创建标签", exact=False)
            if tag.count():
                for t in TAGS:
                    tag.first.click()
                    page.keyboard.type(t, delay=8)
                    time.sleep(0.3)
                    page.keyboard.press("Enter")
                    time.sleep(0.4)
                print("标签 OK", flush=True)
        except Exception as e:
            print("标签失败", e, flush=True)

        # 封面：先点"添加封面"
        n = page.evaluate(CLICK_JS, "添加封面")
        print("点添加封面:", n, flush=True)
        time.sleep(3)
        shot(page, "v7_cover_dialog.png")

        # 弹窗里可能直接有推荐帧，点第一个可点的 img
        picked = page.evaluate("""() => {
          const imgs=[...document.querySelectorAll('img')].filter(im=>{
            const r=im.getBoundingClientRect();
            return r.width>60 && r.height>30 && im.offsetParent!==null;
          });
          if(!imgs.length) return 0;
          imgs[0].scrollIntoView({block:'center'});
          ['mousedown','mouseup','click'].forEach(k=>imgs[0].dispatchEvent(new MouseEvent(k,{bubbles:true,cancelable:true})));
          return imgs.length;
        }""")
        print("封面候选:", picked, flush=True)
        time.sleep(2)
        # 弹窗确认
        for txt in ("确定", "确认", "完成"):
            if page.evaluate(CLICK_JS, txt):
                print("点了确认:", txt, flush=True)
                break
        time.sleep(2)
        shot(page, "v7_after_cover.png")

        # 创作声明
        opened = page.evaluate("""() => {
          const sels=[...document.querySelectorAll('[class*=select]')].filter(e=>e.offsetParent!==null && e.textContent.includes('请选择'));
          if(sels.length){ sels[0].click(); return sels.length; }
          return 0;
        }""")
        time.sleep(1)
        st = page.evaluate(CLICK_JS, STATEMENT)
        print("声明 select/选项:", opened, st, flush=True)
        time.sleep(1)
        shot(page, "v7_before_submit.png")

        # 投稿
        n2 = page.evaluate(CLICK_JS, "立即投稿")
        print("点投稿:", n2, flush=True)
        time.sleep(8)
        shot(page, "v7_after_submit.png")
        txt = page.inner_text("body")
        print("URL:", page.url, flush=True)
        print("成功:", ("投稿成功" in txt) or ("审核" in txt) or ("投递成功" in txt), flush=True)

    finally:
        b.close()


if __name__ == "__main__":
    main()
