import sys, pathlib
sys.path.insert(0, r"E:\RentAGirl\pet")
from PySide6.QtWidgets import QApplication
import pet as petmod

app = QApplication(sys.argv)
p = petmod.Pet()
p.show()
print("images found:", len(p.images), file=sys.stderr)
if p.pic.pixmap() is not None and not p.pic.pixmap().isNull():
    print("pixmap:", p.pic.pixmap().size(), file=sys.stderr)
else:
    print("PIXMAP NULL", file=sys.stderr)
print("geometry:", p.geometry(), "visible:", p.isVisible(), file=sys.stderr)
app.processEvents()
grab = p.grab()
grab.save(r"E:\RentAGirl\out\pet_grab.png")
print("grabbed", grab.size(), file=sys.stderr)
app.quit()
