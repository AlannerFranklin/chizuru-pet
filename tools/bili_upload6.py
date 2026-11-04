"""投稿 v6：全部用 JS 触发点击/输入，绕开可见性限制。"""
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


def js_click_text(page, text):
    return page.evaluate("""(t) => {
      const els = [...document.querySelectorAll('div,span,li,button,a,p')];
      const el = els.find(e => e.textContent.trim() === t && e.offsetParent !== null);
      if (!el) return false;
      el.click();
      return true;
    }""", text)


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
        time.sleep(5)

        # 封面：点系统推荐的第一张
        r = page.evaluate("""() => {
          const imgs=[...document.querySelectorAll('img')];
          const cand=imgs.filter(im=>{const b=im.getBoundingClientRect();return b.width>90&&b.width<220&&b.height>50;});
          if(!cand.length) return 'none';
          const im=cand[cand.length-1];
          ['mousedown','mouseup','click'].forEach(t=>im.dispatchEvent(new MouseEvent(t,{bubbles:true})));
          return cand.length;
        }""")
        print("封面候选/点击:", r, flush=True)
        time.sleep(2)

        # 标题
        page.evaluate("""(t) => {
          const i=document.querySelector('input.input-val');
          if(!i) return false;
          i.focus(); i.value=''; i.dispatchEvent(new Event('input',{bubbles:true}));
          return true;
        }""", TITLE)
        ti = page.query_selector("input.input-val")
        if ti:
            ti.click()
            page.keyboard.type(TITLE, delay=8)
            print("标题 OK", flush=True)

        # 简介
        ok = page.evaluate("""(d) => {
          const tas=[...document.querySelectorAll('textarea')];
          const ta=tas[tas.length-1];
          if(!ta) return false;
          ta.focus();
          ta.value=d;
          ta.dispatchEvent(new Event('input',{bubbles:true}));
          ta.dispatchEvent(new Event('change',{bubbles:true}));
          return true;
        }""", DESC)
        print("简介 JS:", ok, flush=True)

        # 标签
        for t in TAGS:
            try:
                page.evaluate("""(t)=>{
                  const i=[...document.querySelectorAll('input')].find(x=>(x.placeholder||'').includes('回车'));
                  if(!i) return false; i.focus(); return true;
                }""", t)
                page.keyboard.type(t, delay=8)
                time.sleep(0.3)
                page.keyboard.press("Enter")
                time.sleep(0.4)
            except Exception:
                pass
        print("标签 OK", flush=True)

        # 创作声明
        page.evaluate("""() => {
          const s=[...document.querySelectorAll('div')].find(d=>(d.className||'').toString().includes('select') && d.offsetParent!==null);
          if(s) s.click();
        }""")
        time.sleep(1)
        ok2 = js_click_text(page, STATEMENT)
        print("声明:", ok2, flush=True)
        time.sleep(1)
        shot(page, "v6_1.png")

        # 投稿
        clicked = js_click_text(page, "立即投稿")
        print("投稿点击:", clicked, flush=True)
        for _ in range(10):
            time.sleep(3)
            txt = page.inner_text("body")
            if "投稿成功" in txt or "审核" in txt or "成功" in txt:
                break
        shot(page, "v6_2.png")
        txt = page.inner_text("body")
        print("URL:", page.url, flush=True)
        print("成功?", ("投稿成功" in txt) or ("审核" in txt), flush=True)

    finally:
        b.close()


if __name__ == "__main__":
    main()
