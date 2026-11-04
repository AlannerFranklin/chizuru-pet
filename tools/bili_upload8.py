"""投稿 v8：完整流程 + 明确的封面/创作声明处理。"""
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
        "水原千鶴（一ノ瀬千鶴）の自己紹介です。声・絵・編集はすべてローカル環境で生成しています。\n"
        "#水原千鹤 #租借女友 #二次元")
TAGS = ["水原千鹤", "租借女友", "二次元"]
STATEMENT = "含AI生成内容"


def shot(page, name):
    try:
        page.screenshot(path=str(SHOT / name), full_page=True)
        print("  shot", name, flush=True)
    except Exception:
        pass


def js(page, code, *args):
    return page.evaluate(code, *args)


def click_by_text(page, text, exact=True):
    return js(page, """([t, exact]) => {
      const els=[...document.querySelectorAll('div,span,button,li,a')].filter(e=>{
        if (e.offsetParent===null) return false;
        const s=e.textContent.trim();
        return exact ? s===t : s.includes(t);
      });
      if(!els.length) return 0;
      const el=els[els.length-1];
      el.scrollIntoView({block:'center'});
      ['mousedown','mouseup','click'].forEach(k=>el.dispatchEvent(new MouseEvent(k,{bubbles:true,cancelable:true})));
      return els.length;
    }""", [text, exact])


def main():
    b = Bili()
    page = b.page
    try:
        b.goto(URL, wait=8)
        page.bring_to_front()
        time.sleep(4)
        cdp = page.context.new_cdp_session(page)
        ok = False
        for _ in range(15):
            try:
                doc = cdp.send("DOM.getDocument", {"depth": 1})
                n = cdp.send("DOM.querySelector", {"nodeId": doc["root"]["nodeId"], "selector": "input[type=file]"})
                if n.get("nodeId"):
                    cdp.send("DOM.setFileInputFiles", {"files": [str(VIDEO)], "nodeId": n["nodeId"]})
                    ok = True
                    break
            except Exception:
                pass
            time.sleep(2)
        print("文件已选:", ok, flush=True)

        t0 = time.time()
        while time.time() - t0 < 600:
            if "上传完成" in page.inner_text("body"):
                break
            time.sleep(3)
        page.bring_to_front()
        time.sleep(6)
        print("上传完成", flush=True)

        # 标题
        ti = page.query_selector("input.input-val")
        ti.click()
        ti.fill("")
        ti.type(TITLE, delay=8)
        print("标题 OK", flush=True)

        # 简介
        ed = page.query_selector(".ql-editor")
        ed.click()
        page.keyboard.type(DESC, delay=1)
        print("简介 OK", flush=True)

        # 标签
        tag = page.get_by_placeholder("按回车键Enter创建标签", exact=False)
        if tag.count():
            for t in TAGS:
                tag.first.click()
                page.keyboard.type(t, delay=8)
                time.sleep(0.3)
                page.keyboard.press("Enter")
                time.sleep(0.4)
        print("标签 OK", flush=True)

        # 封面
        click_by_text(page, "添加封面")
        time.sleep(3)
        n = js(page, """() => {
          const imgs=[...document.querySelectorAll('img')].filter(im=>{
            const r=im.getBoundingClientRect();
            return r.width>70 && r.height>40 && im.offsetParent!==null;
          });
          if(!imgs.length) return 0;
          imgs[0].scrollIntoView({block:'center'});
          ['mousedown','mouseup','click'].forEach(k=>imgs[0].dispatchEvent(new MouseEvent(k,{bubbles:true,cancelable:true})));
          return imgs.length;
        }""")
        print("封面候选/点击:", n, flush=True)
        time.sleep(2)
        for t in ("完成", "确定", "确认"):
            if click_by_text(page, t):
                print("封面确认:", t, flush=True)
                break
        time.sleep(2)
        shot(page, "v8_cover.png")

        # 创作声明
        opened = js(page, """() => {
          const s=[...document.querySelectorAll('[class*=select]')].filter(e=>e.offsetParent!==null);
          for (const el of s){
            if (el.textContent.includes('请选择') || el.className.includes('bcc-select')){
              el.click(); return el.className;
            }
          }
          return '';
        }""")
        time.sleep(1.5)
        picked = js(page, """(t) => {
          const opts=[...document.querySelectorAll('li.bcc-option, .bcc-option')].filter(e=>e.offsetParent!==null);
          const el=opts.find(e=>e.textContent.trim()===t);
          if(!el) return 0;
          el.click(); return opts.length;
        }""", STATEMENT)
        print("声明:", opened[:30] if opened else "-", picked, flush=True)
        time.sleep(1)
        shot(page, "v8_before_submit.png")

        # 投稿
        n2 = click_by_text(page, "立即投稿")
        print("点投稿:", n2, flush=True)
        for _ in range(12):
            time.sleep(3)
            txt = page.inner_text("body")
            if ("投递成功" in txt) or ("投稿成功" in txt) or ("审核" in txt) or ("稿件" in txt and "成功" in txt):
                break
        shot(page, "v8_after_submit.png")
        print("最终 URL:", page.url, flush=True)
        txt = page.inner_text("body")
        print("含成功字样:", any(k in txt for k in ("投递成功", "投稿成功", "审核中")), flush=True)

    finally:
        b.close()


if __name__ == "__main__":
    main()
