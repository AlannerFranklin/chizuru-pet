import sys, time, pathlib
sys.path.insert(0, r"E:\RentAGirl\pet")
from PySide6.QtWidgets import QApplication
import pet as petmod

app = QApplication(sys.argv)
p = petmod.Pet(demo=True)
p.show()
before = {f.name for f in (pathlib.Path(r"E:\RentAGirl\out\voice")).glob("*.wav")}
p.say({"ja": "そんなこと言われても、困るんだけど", "zh": "你这么说我会很为难的", "mode": "素"})
t0 = time.time()
new = None
while time.time() - t0 < 40:
    after = {f.name for f in (pathlib.Path(r"E:\RentAGirl\out\voice")).glob("*.wav")}
    if after - before:
        new = after - before
        break
    app.processEvents()
    time.sleep(0.2)
print("new wav:", new, "elapsed", round(time.time() - t0, 1), "s")
app.quit()
