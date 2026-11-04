import sys, pathlib
sys.path.insert(0, r"E:\RentAGirl\pet")
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
import pet as petmod
import brain

q = sys.argv[1] if len(sys.argv) > 1 else "今日ちょっと疲れた"
out = pathlib.Path(sys.argv[2]) if len(sys.argv) > 2 else pathlib.Path(r"E:\RentAGirl\out\pet_chat.png")

app = QApplication(sys.argv)
p = petmod.Pet(demo=True)
p.show()
r = brain.reply(q)
print("Q:", q)
print("A:", r["ja"], "|", r["zh"], "|", r["mode"])
p.set_mood(r.get("mode", "素"))
p.bubble.show_text(r.get("ja", ""), r.get("zh", ""), r.get("mode", "素"), ms=60000)
QTimer.singleShot(600, lambda: (QApplication.processEvents(), p.grab().save(str(out)), app.quit()))
app.exec()
print("saved", out)
