import sys
sys.path.insert(0, r"E:\RentAGirl\pet")
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
import pet as petmod

app = QApplication(sys.argv)
s = app.primaryScreen()
print("geometry", s.geometry(), "available", s.availableGeometry(), "dpr", s.devicePixelRatio(), file=sys.stderr)
p = petmod.Pet()
p.move(120, 120)
p.show()
print("pet geom", p.geometry(), file=sys.stderr)
QTimer.singleShot(8000, app.quit)
app.exec()
