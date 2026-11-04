"""打开一个专用 Chrome 窗口（独立配置目录），供登录 B 站。
登录状态会保存在 E:\\RentAGirl\\chrome-profile，之后自动化都复用这个目录。
用法: python bili_login.py
"""
import pathlib
import time

from playwright.sync_api import sync_playwright

PROFILE = pathlib.Path(r"E:\RentAGirl\chrome-profile")
PROFILE.mkdir(parents=True, exist_ok=True)
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"


def logged_in(ctx):
    for c in ctx.cookies("https://www.bilibili.com"):
        if c["name"] == "SESSDATA" and c.get("value"):
            return True
    return False


def main():
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            user_data_dir=str(PROFILE),
            executable_path=CHROME,
            headless=False,
            viewport={"width": 1280, "height": 860},
            args=["--disable-blink-features=AutomationControlled"],
        )
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        page.goto("https://www.bilibili.com", wait_until="domcontentloaded")
        print("已打开 B 站，请在里面扫码/密码登录（最多等 10 分钟）", flush=True)
        deadline = time.time() + 600
        while time.time() < deadline:
            if logged_in(ctx):
                print("LOGIN_OK 已登录，配置已保存", flush=True)
                time.sleep(2)
                ctx.close()
                return
            time.sleep(3)
        print("TIMEOUT 还没登录，窗口先留着；登录后状态也会自动保存", flush=True)
        ctx.close()


if __name__ == "__main__":
    main()
