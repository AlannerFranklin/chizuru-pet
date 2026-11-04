"""生活循环（无界面版）：常驻或单次运行。核心逻辑在 pet/life_core.py。"""
import argparse
import random
import sys
import time

sys.path.insert(0, r"E:\RentAGirl\pet")
import life_core


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--once", action="store_true")
    args = ap.parse_args()
    if args.once:
        print(life_core.wake_once())
        return
    print("生活循环（无界面）启动", flush=True)
    while True:
        try:
            now = time.localtime()
            wait = random.randint(90, 150) * 60 if 1 <= now.tm_hour < 7 else random.randint(22, 45) * 60
            time.sleep(wait)
            life_core.wake_once()
        except Exception as e:
            print("循环出错:", type(e).__name__, str(e)[:120], flush=True)
            time.sleep(300)


if __name__ == "__main__":
    main()