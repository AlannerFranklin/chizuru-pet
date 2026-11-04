"""水原千鹤 桌宠 v0.4
- 单张立绘（透明背景），可拖动、置顶
- 自定义绘制 + 60fps 呼吸动画（只重绘立绘区域，不整窗刷新）
- 双击打开输入框；右键菜单（静音 / 说一句 / 退出）
- 气泡：中文大字 + 日文小字，边框颜色随情绪
"""
import math
import random
import json
import re
import ctypes
import ctypes.wintypes
import sys
import pathlib
import time
import queue
import threading

from PySide6.QtCore import Qt, QTimer, QRectF, QPoint, QElapsedTimer, QAbstractNativeEventFilter
from PySide6.QtGui import (QPixmap, QPainter, QColor, QFont, QPen,
                           QPainterPath, QGuiApplication)
from PySide6.QtWidgets import QApplication, QWidget, QLineEdit, QMenu

ROOT = pathlib.Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets_v3"
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import brain

W, H = 380, 760
BUBBLE_H = 122
IMG_H = 560
FPS = 60

PRIO_BELOW = -1
PRIO_ABOVE = 1


def _thread_priority(value):
    """给当前线程设优先级：UI 高一点，干活的低一点，避免抢 GIL 卡界面。"""
    try:
        import ctypes
        ctypes.windll.kernel32.SetThreadPriority(
            ctypes.windll.kernel32.GetCurrentThread(), int(value))
    except Exception:
        pass
MOOD_COLOR = {
    "素": QColor(230, 150, 170),
    "営業": QColor(240, 170, 120),
    "衝突": QColor(220, 90, 90),
    "软肋": QColor(140, 150, 200),
}

SETTINGS = pathlib.Path(__file__).resolve().parent / "settings.json"
CHANGE_VIDEO = re.compile(r"(换个|换一个|换一换|换别的|不要这|不看了|不喜欢这|下一个|别的视频|other)")
HOTKEY_ID = 0xB001


class HotkeyFilter(QAbstractNativeEventFilter):
    """全局快捷键 Ctrl+Alt+Z：打开聊天输入框。"""

    def __init__(self, on_hotkey):
        super().__init__()
        self.on_hotkey = on_hotkey

    def nativeEventFilter(self, eventType, message):
        try:
            if eventType == b"windows_generic_MSG":
                msg = ctypes.wintypes.MSG.from_address(int(message))
                if msg.message == 0x0312 and msg.wParam == HOTKEY_ID:
                    self.on_hotkey()
        except Exception:
            pass
        return False, 0


def register_hotkey():
    MOD_ALT, MOD_CONTROL, MOD_NOREPEAT = 0x0001, 0x0002, 0x4000
    try:
        ctypes.windll.user32.RegisterHotKey(None, HOTKEY_ID, MOD_CONTROL | MOD_ALT | MOD_NOREPEAT, ord("Z"))
        return True
    except Exception:
        return False


def unregister_hotkey():
    try:
        ctypes.windll.user32.UnregisterHotKey(None, HOTKEY_ID)
    except Exception:
        pass


def _load_settings():
    try:
        return json.loads(SETTINGS.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_settings(d):
    try:
        SETTINGS.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass


class Bubble(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ja = ""
        self.zh = ""
        self.mood = "素"
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.hide()

    def show_text(self, ja, zh, mood="素", ms=9000):
        self.ja, self.zh, self.mood = ja, zh, mood
        self.show()
        self.update()
        QTimer.singleShot(ms, self.hide)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        rect = QRectF(4, 4, self.width() - 12, self.height() - 14)
        path = QPainterPath()
        path.addRoundedRect(rect, 14, 14)
        p.setPen(QPen(MOOD_COLOR.get(self.mood, QColor(230, 150, 170)), 2.5))
        p.setBrush(QColor(255, 255, 255, 242))
        p.drawPath(path)

        r = rect.adjusted(13, 9, -13, -9)
        p.setFont(QFont("Microsoft YaHei", 12))
        p.setPen(QColor(45, 45, 45))
        fm = p.fontMetrics()
        zh_h = min(fm.boundingRect(0, 0, int(r.width()), 10000, Qt.TextWordWrap, self.zh).height(), 76)
        p.drawText(QRectF(r.left(), r.top(), r.width(), zh_h + 4),
                   Qt.TextWordWrap | Qt.AlignLeft | Qt.AlignTop, self.zh)

        p.setFont(QFont("Yu Gothic UI", 9))
        p.setPen(QColor(150, 150, 150))
        p.drawText(QRectF(r.left(), r.top() + zh_h + 6, r.width(), r.height() - zh_h - 6),
                   Qt.TextWordWrap | Qt.AlignLeft | Qt.AlignTop, self.ja)


class Pet(QWidget):
    def __init__(self, demo=False):
        super().__init__()
        self.demo = demo
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(W, H)

        self.images = sorted(ASSETS.glob("*.png"))
        self.idx = 0
        self.drag_pos = None
        self.t = 0.0
        self.bounce = 0.0
        self._last_off = (0, 1.0)
        self.anim_mode = _load_settings().get("anim", "sway")
        self.sway_left = 0.0
        self.sway_total = 0.8
        self.sway_timer = 5.0
        self.pix = None
        self.pic_rect = None
        self.load_image()

        self.bubble = Bubble(self)
        self.bubble.setGeometry(6, 2, W - 12, BUBBLE_H - 6)

        self.input = QLineEdit(self)
        self.input.setPlaceholderText("和她说点什么…（回车发送 / Esc 关闭）")
        self.input.setGeometry(20, H - 40, W - 40, 32)
        self.input.setStyleSheet(
            "QLineEdit{background:rgba(255,255,255,245);border:2px solid #e696aa;"
            "border-radius:16px;padding:4px 12px;font-size:13px;}")
        self.input.hide()
        self.input.returnPressed.connect(self.on_send)

        # 按显示器刷新率跑动画：只更新立绘所在的矩形
        rate = FPS
        try:
            scr = self.screen() or QGuiApplication.primaryScreen()
            r = float(scr.refreshRate()) if scr else 0.0
            if r >= 30:
                rate = int(round(r))
        except Exception:
            pass
        want = _load_settings().get("fps")
        if isinstance(want, int) and want >= 30:
            rate = want
        self.fps = max(30, min(rate, 360))
        self.elapsed = QElapsedTimer()
        self.elapsed.start()
        self.anim = QTimer(self)
        self.anim.timeout.connect(self.on_tick)
        self.anim.setTimerType(Qt.PreciseTimer)
        self.anim.setInterval(max(1, int(round(1000.0 / self.fps))))
        self.anim.start()

        # 自主生活：由她自己决定什么时候做什么，做完在气泡里说出来
        self.life_busy = False
        self.life_timer = QTimer(self)
        self.life_timer.timeout.connect(self.life_tick)
        self.life_timer.start(60 * 1000)
        self._life_next = 0.0

        if not demo:
            self.move_to_corner()

    # ---------- 自主生活 ----------
    def life_tick(self):
        import time as _t
        if self.life_busy:
            return
        now = _t.time()
        if now < self._life_next:
            return
        try:
            import random as _r
            hour = _t.localtime().tm_hour
            wait = _r.randint(90, 150) * 60 if 1 <= hour < 7 else _r.randint(22, 45) * 60
            self._life_next = now + wait
        except Exception:
            self._life_next = now + 1800
        self.life_busy = True

        def work():
            try:
                import life_core
                rec = life_core.wake_once()
            except Exception as e:
                print("life err:", e)
                rec = None
            self._life_q = getattr(self, "_life_q", None)
            try:
                self.bubble_q.put(rec)
            except Exception:
                pass

        import threading
        if not hasattr(self, "bubble_q"):
            self.bubble_q = queue.Queue()
            QTimer.singleShot(1000, self._poll_life)
        threading.Thread(target=work, daemon=True).start()

    def _poll_life(self):
        try:
            rec = self.bubble_q.get_nowait()
        except Exception:
            rec = "empty"
        if rec != "empty":
            self.life_busy = False
            if rec:
                actions = rec.get("actions") or []
                zh_map = {
                    "bili_browse": "去 B 站逛了逛",
                    "bili_comment": "在 B 站发了条评论",
                    "write_diary": "写了一段日记",
                    "message_user": "给你发了条微信",
                    "study": "练了一会儿台词",
                    "rest": "歇了一会儿",
                }
                doing = "、".join(zh_map.get(a, a) for a in actions) or "发呆"
                self.bubble.show_text(f"いま…{doing}", f"（她{doing}）", "素", ms=9000)
        QTimer.singleShot(2000, self._poll_life)

    def load_image(self):
        if not self.images:
            return
        pix = QPixmap(str(self.images[self.idx % len(self.images)]))
        base = pix.scaledToHeight(IMG_H, Qt.SmoothTransformation)
        self.pix = base
        # 预渲染呼吸帧（1.000~1.010 共 25 档）：运行时只 blit，不再逐帧重采样
        self.frames = []
        for k in range(25):
            s = 1.0 + 0.010 * k / 24
            self.frames.append(base.scaled(max(1, int(round(base.width() * s))),
                                           max(1, int(round(base.height() * s))),
                                           Qt.IgnoreAspectRatio, Qt.SmoothTransformation))
        x = (W - base.width()) // 2
        self.pic_rect = (x, BUBBLE_H + 4, base.width(), base.height())
        self.update()

    def move_to_corner(self):
        s = QGuiApplication.primaryScreen().availableGeometry()
        self.move(s.left() + 40, max(0, s.bottom() - H - 10))

    def current_dy(self):
        """按动画模式算出整数像素偏移。"""
        dy = 0.0
        if self.anim_mode == "sway" and self.sway_left > 0:
            prog = 1.0 - self.sway_left / self.sway_total
            dy += 3.0 * math.sin(math.pi * prog)
        elif self.anim_mode == "breathe":
            dy += 2.2 * math.sin(2 * math.pi * self.t / 4.0)
        dy -= self.bounce
        return int(round(dy)), 0.0

    def current_scale(self):
        if self.anim_mode == "breathe":
            return 1.0 + 0.010 * math.sin(2 * math.pi * self.t / 4.0)
        return 1.0

    def on_tick(self):
        dt = self.elapsed.restart() / 1000.0
        # 卡顿诊断：定时器实际间隔远大于预期，说明 UI 线程被别的活堵住了
        try:
            if not hasattr(self, "_lag_max"):
                self._lag_max = 0.0
                self._lag_t0 = time.time()
            self._lag_max = max(self._lag_max, dt)
            if time.time() - self._lag_t0 > 5:
                if self._lag_max > 0.4:
                    with open(r"E:\RentAGirl\out\pet_ui.log", "a", encoding="utf-8") as f:
                        f.write(f"{time.strftime('%H:%M:%S')} 最长间隔 {self._lag_max*1000:.0f}ms\n")
                self._lag_max = 0.0
                self._lag_t0 = time.time()
        except Exception:
            pass
        if dt <= 0 or dt > 0.25:
            dt = 1.0 / self.fps
        self.t += dt
        if self.bounce > 0:
            self.bounce = max(0.0, self.bounce - 550.0 * dt / 16.0)
        if self.sway_left > 0:
            self.sway_left = max(0.0, self.sway_left - dt)
        if self.anim_mode == "sway":
            self.sway_timer -= dt
            if self.sway_timer <= 0 and self.sway_left == 0:
                self.sway_left = self.sway_total = 0.8
                self.sway_timer = 7.0 + random.uniform(-2.5, 3.5)

        dy, _ = self.current_dy()
        s = self.current_scale()
        key = (dy, round(s, 3))
        if key != self._last_off:
            self._last_off = key
            if self.pic_rect:
                x, y, w, h = self.pic_rect
                self.update(x - 8, y - 14, w + 16, h + 24)

    def paintEvent(self, _):
        if not self.pix or not self.pic_rect:
            return
        p = QPainter(self)
        x, y, w, h = self.pic_rect
        dy, _ = self.current_dy()
        s = self.current_scale()
        if s == 1.0:
            p.drawPixmap(x, y - dy, self.pix)
        else:
            # 连续缩放（平滑重采样，视觉最自然）
            p.setRenderHint(QPainter.SmoothPixmapTransform)
            nw, nh = w * s, h * s
            p.drawPixmap(QRectF(x + (w - nw) / 2.0, y - dy + (h - nh), nw, nh),
                         self.pix, QRectF(self.pix.rect()))

    def pop(self):
        self.bounce = 6.0

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.drag_pos = e.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, e):
        if self.drag_pos is not None and e.buttons() & Qt.LeftButton:
            self.move(e.globalPosition().toPoint() - self.drag_pos)

    def mouseReleaseEvent(self, e):
        self.drag_pos = None

    def mouseDoubleClickEvent(self, e):
        # 打开输入框时暂停呼吸动画，避免同时刷新造成卡顿
        self.anim.stop()
        self.input.show()
        self.input.setFocus()

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Escape:
            self.input.hide()
            self._resume_anim()
        super().keyPressEvent(e)

    def _resume_anim(self):
        if not self.anim.isActive():
            self.elapsed.restart()
            self.anim.start()

    def contextMenuEvent(self, e):
        menu = QMenu(self)
        menu.setStyleSheet("QMenu{background:white;border:1px solid #e696aa;}"
                           "QMenu::item:selected{background:#fde3ea;}")
        self.voice_on = getattr(self, "voice_on", True)
        a2 = menu.addAction("让她说一句")
        a5 = menu.addAction("去逛 B 站")
        a4 = menu.addAction("静音" if self.voice_on else "开声音")
        anim_menu = menu.addMenu("动画")
        cur = self.anim_mode
        a_static = anim_menu.addAction(("✓ " if cur == "static" else "") + "静止（只有说话时动）")
        a_sway = anim_menu.addAction(("✓ " if cur == "sway" else "") + "偶尔轻晃（清晰）")
        a_breath = anim_menu.addAction(("✓ " if cur == "breathe" else "") + "持续呼吸（会略糊）")
        fps_menu = menu.addMenu("帧率")
        cur_fps = _load_settings().get("fps", 170)
        a_fps = {}
        for label, val in [("60", 60), ("120", 120), ("170（跟屏幕）", 170), ("跟随屏幕", 0)]:
            a = fps_menu.addAction(("✓ " if cur_fps == (val or None) else "") + label)
            a_fps[a] = val
        menu.addSeparator()
        a_ws = menu.addAction("打开她的工作区")
        a3 = menu.addAction("退出")
        act = menu.exec(e.globalPos())
        if act == a2:
            self.idle_line()
        elif act == a_ws:
            import subprocess
            subprocess.Popen(["explorer", r"E:\RentAGirl\workspace\chizuru"])
        elif act == a5:
            self.browse_bili()
        elif act == a4:
            self.voice_on = not self.voice_on
        elif act in a_fps:
            d = _load_settings()
            d["fps"] = a_fps[act] or int(round(self.screen().refreshRate()))
            _save_settings(d)
            self.fps = max(30, min(d["fps"], 360))
            self.anim.setInterval(max(1, int(round(1000.0 / self.fps))))
        elif act in (a_static, a_sway, a_breath):
            self.anim_mode = {a_static: "static", a_sway: "sway", a_breath: "breathe"}[act]
            d = _load_settings()
            d["anim"] = self.anim_mode
            _save_settings(d)
            self._last_off = (999, 1.0)
            self.update()
        elif act == a3:
            QApplication.quit()

    def browse_bili(self):
        if getattr(self, "_bili_running", False):
            self.say({"ja": "いま見てるところ、ちょっと待って", "zh": "我正在看啦，等一会儿", "mode": "素"})
            return
        self._bili_running = True
        self._bili_q = queue.Queue()
        self.say({"ja": "ちょっと……何見ようかな", "zh": "让我想想看点什么…", "mode": "素"})

        def work():
            _thread_priority(PRIO_BELOW)
            try:
                import bili
                r = bili.run()
            except Exception as e:
                print("bili err:", e)
                r = None
            self._bili_q.put(r)

        threading.Thread(target=work, daemon=True).start()

        def poll():
            try:
                r = self._bili_q.get_nowait()
            except queue.Empty:
                QTimer.singleShot(400, poll)
                return
            self._bili_running = False
            if r:
                self.say({"ja": r["ja"], "zh": r["zh"], "mode": "素"})
                print("B站:", r.get("keyword"), "|", r.get("title"))
            else:
                self.say({"ja": "うまく見られなかったみたい", "zh": "好像没看成…", "mode": "素"})

        QTimer.singleShot(400, poll)

    def say(self, r):
        # 气泡先显示（不自动消失），等语音合成好后按音频时长再收
        self.bubble.show_text(r.get("ja", ""), r.get("zh", ""), r.get("mode", "素"), ms=600000)
        self.pop()
        wav = None
        if getattr(self, "voice_on", True):
            try:
                import voice
                wav = voice.speak(r.get("ja", ""))
            except Exception as e:
                print("voice error:", e)
        self._schedule_hide(wav)

    def _schedule_hide(self, wav, tries=0):
        """语音开始后按实际时长 + 0.5 秒收起气泡。"""
        import soundfile as sf
        if wav:
            try:
                p = pathlib.Path(str(wav))
                if p.exists():
                    d = sf.info(str(p)).duration
                    QTimer.singleShot(int((d + 0.5) * 1000), self.bubble.hide)
                    return
            except Exception:
                pass
        if tries < 120:
            QTimer.singleShot(100, lambda: self._schedule_hide(wav, tries + 1))
        else:
            QTimer.singleShot(5000, self.bubble.hide)

    def on_send(self):
        text = self.input.text().strip()
        if not text:
            return
        self.input.clear()
        self.input.hide()
        self._resume_anim()
        # 让 agent 在后台跑，界面不卡（有可能要搜索/写代码/逛站，耗时几十秒）
        self._chat_q = queue.Queue()
        self.bubble.show_text("……", "稍等，我看一下", "素", ms=600000)

        def work():
            _thread_priority(PRIO_BELOW)
            try:
                r = brain.reply_agent(text)
            except Exception as e:
                print("agent err:", e)
                r = None
            self._chat_q.put(r)

        threading.Thread(target=work, daemon=True).start()

        def poll():
            try:
                r = self._chat_q.get_nowait()
            except queue.Empty:
                QTimer.singleShot(250, poll)
                return
            if r:
                self.say(r)
            else:
                self.bubble.hide()

        QTimer.singleShot(250, poll)

    def idle_line(self):
        self.say(brain.idle())

    def render_preview(self, path):
        self.bubble.show_text("恋人です", "我们是情侣", "営業", ms=60000)
        QApplication.processEvents()
        self.grab().save(str(path))


def _preload():
    """后台预加载重模块，避免第一次回车时卡一下。"""
    try:
        import soundfile  # noqa: F401
    except Exception:
        pass
    try:
        import voice  # noqa: F401
    except Exception:
        pass
    try:
        import actions  # noqa: F401
    except Exception:
        pass
    try:
        import web  # noqa: F401
    except Exception:
        pass


def main():
    demo = "--demo" in sys.argv
    if not demo:
        # 单实例：用命名互斥量，已经有她在跑就直接退出
        import ctypes
        global _MUTEX
        _MUTEX = ctypes.windll.kernel32.CreateMutexW(None, False, "Global\\ChizuruPetMutex")
        if ctypes.windll.kernel32.GetLastError() == 183:   # ERROR_ALREADY_EXISTS
            print("已经有一个她在运行了")
            return
    app = QApplication(sys.argv)
    _thread_priority(PRIO_ABOVE)
    p = Pet(demo=demo)
    p.show()
    if not demo:
        threading.Thread(target=_preload, daemon=True).start()
        try:
            import voice
            voice.warmup()
        except Exception:
            pass
        # 全局快捷键 Ctrl+Alt+Z 打开/关闭输入框
        hk = HotkeyFilter(lambda: (p.input.show(), p.input.setFocus(),
                                   p.anim.stop()) if not p.input.isVisible() else (p.input.hide(), p._resume_anim()))
        app.installNativeEventFilter(hk)
        register_hotkey()
        app.aboutToQuit.connect(unregister_hotkey)
    if demo:
        QTimer.singleShot(700, lambda: (p.render_preview(ROOT / "out" / "pet_preview.png"), app.quit()))
        app.exec()
        print("preview saved")
        return
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
