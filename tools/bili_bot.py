"""B 站自动化：浏览、看视频信息、发评论（复用登录过的 Chrome 配置）。
没开浏览器时会自动用调试端口拉起专用 Chrome。
"""
import pathlib
import re
import subprocess
import time
import urllib.request

from playwright.sync_api import sync_playwright

CDP = "http://127.0.0.1:9222"
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
PROFILE = r"E:\RentAGirl\chrome-profile"
CREATE_NO_WINDOW = 0x08000000


def cdp_alive(timeout=2):
    try:
        with urllib.request.urlopen(CDP + "/json/version", timeout=timeout) as r:
            return r.status == 200
    except Exception:
        return False


def ensure_chrome(wait=25):
    """确保有一个带调试端口的 Chrome 在跑（没开就自己拉起来）。"""
    if cdp_alive():
        return True
    try:
        subprocess.Popen([CHROME, "--remote-debugging-port=9222",
                          f"--user-data-dir={PROFILE}",
                          "--no-first-run", "--no-default-browser-check",
                          "https://www.bilibili.com"],
                         creationflags=CREATE_NO_WINDOW, close_fds=True)
    except Exception as e:
        print("启动 Chrome 失败:", e)
        return False
    t0 = time.time()
    while time.time() - t0 < wait:
        if cdp_alive():
            time.sleep(1.5)
            return True
        time.sleep(0.8)
    return False


class Bili:
    """连接到带调试端口的 Chrome（同一个窗口，登录状态共享）。没开就自动拉起来。"""

    def __init__(self, headless=False):
        if not cdp_alive():
            print("浏览器没开，自动启动…", flush=True)
            ensure_chrome()
        self._p = sync_playwright().start()
        self.browser = self._p.chromium.connect_over_cdp(CDP)
        self.ctx = self.browser.contexts[0]
        self.page = self.ctx.pages[0] if self.ctx.pages else self.ctx.new_page()

    # ---------- 基础 ----------
    def goto(self, url, wait=2.0):
        self.page.goto(url, wait_until="domcontentloaded", timeout=45000)
        time.sleep(wait)
        return self.page

    def logged_in(self):
        for c in self.ctx.cookies("https://www.bilibili.com"):
            if c["name"] == "SESSDATA" and c.get("value"):
                return True
        return False

    # ---------- 浏览 ----------
    def home_titles(self, limit=12):
        self.goto("https://www.bilibili.com")
        time.sleep(2)
        items = self.page.eval_on_selector_all(
            ".bili-video-card__info--tit, .bili-video-card__info--tit a",
            "els => els.map(e => (e.innerText || e.getAttribute('title') || '').trim()).filter(Boolean)",
        )
        return items[:limit]

    def search(self, q, limit=10):
        self.goto(f"https://search.bilibili.com/all?keyword={q}")
        time.sleep(3)
        items = self.page.eval_on_selector_all(
            ".bili-video-card__info--tit",
            "els => els.map(e => e.innerText.trim()).filter(Boolean)",
        )
        return items[:limit]

    def open_video(self, url):
        self.goto(url, wait=3)
        return self.video_info()

    def video_info(self):
        title = ""
        for sel in ["h1.video-title", "h1[title]", ".video-title"]:
            try:
                el = self.page.query_selector(sel)
                if el:
                    title = (el.get_attribute("title") or el.inner_text()).strip()
                    if title:
                        break
            except Exception:
                pass
        desc = ""
        try:
            el = self.page.query_selector(".desc-info-text, .basic-desc-info")
            if el:
                desc = el.inner_text().strip()[:400]
        except Exception:
            pass
        bvid = ""
        m = re.search(r"(BV[0-9A-Za-z]+)", self.page.url + " " + self.page.content()[:5000])
        if m:
            bvid = m.group(1)
        return {"url": self.page.url, "bvid": bvid, "title": title, "desc": desc}

    def top_comments(self, n=8):
        time.sleep(2)
        try:
            self.page.evaluate("window.scrollBy(0, 900)")
            time.sleep(1.5)
        except Exception:
            pass
        items = self.page.eval_on_selector_all(
            ".reply-content, .reply-item .reply-content",
            "els => els.map(e => e.innerText.trim()).filter(Boolean)",
        )
        return items[:n]

    # ---------- 互动 ----------
    def like(self):
        try:
            el = self.page.query_selector(".video-like")
            if not el:
                return False
            if "on" in (el.get_attribute("class") or "").split():
                return True
            el.click()
            time.sleep(1.2)
            cls2 = (self.page.query_selector(".video-like").get_attribute("class") or "")
            return "on" in cls2.split()
        except Exception as e:
            print("like err", e)
            return False

    def favorite(self):
        try:
            el = self.page.query_selector(".video-fav")
            if el and "on" in (el.get_attribute("class") or "").split():
                return True
            if el:
                el.evaluate("e => e.click()")
            time.sleep(1.5)
            box = self.page.query_selector(".collection-m-exp input[type='checkbox']")
            if box:
                box.evaluate("e => { e.checked = true; e.dispatchEvent(new Event('change', {bubbles:true})); e.click(); }")
                time.sleep(0.6)
            btn = self.page.query_selector(".collection-m-exp .btn.submit-move")
            if btn:
                btn.evaluate("e => e.click()")
                time.sleep(1.5)
                return True
            return False
        except Exception as e:
            print("fav err", e)
            return False
        finally:
            try:
                # 万一弹窗没关掉，按 Esc 收掉
                if self.page.query_selector(".collection-m-exp"):
                    self.page.keyboard.press("Escape")
                    time.sleep(0.5)
            except Exception:
                pass

    def post_comment(self, text):
        self.page.evaluate("window.scrollTo(0, document.body.scrollHeight * 0.55)")
        time.sleep(2)
        box = None
        for sel in [".brt-editor", "div[contenteditable='true']", "textarea.bili-comment-input"]:
            try:
                box = self.page.query_selector(sel)
                if box:
                    break
            except Exception:
                pass
        if not box:
            return False, "找不到评论输入框（可能没登录或被限制）"
        box.click()
        time.sleep(0.5)
        box.type(text, delay=25)
        time.sleep(0.8)
        try:
            for b_ in self.page.query_selector_all("button, div[role='button']"):
                try:
                    if (b_.inner_text() or "").strip() == "发布":
                        b_.click()
                        time.sleep(2.5)
                        return True, "已发送"
                except Exception:
                    continue
        except Exception:
            pass
        return False, "找不到发布按钮"

    def close(self):
        try:
            self.browser.close()
        except Exception:
            pass
        finally:
            self._p.stop()


if __name__ == "__main__":
    b = Bili(headless=False)
    print("logged in:", b.logged_in())
    print("首页标题:")
    for t in b.home_titles(8):
        print("  -", t)
    b.close()
