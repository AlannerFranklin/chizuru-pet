import sys
from PySide6.QtWidgets import QApplication, QWidget, QLabel
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPixmap

app = QApplication(sys.argv)

# 1) 普通不透明窗口
w1 = QWidget()
w1.setWindowTitle("plain")
w1.resize(200, 200)
w1.move(100, 200)
w1.setStyleSheet("background:#ff6666;")
w1.show()

# 2) 透明无边框窗口
w2 = QWidget()
w2.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
w2.setAttribute(Qt.WA_TranslucentBackground)
w2.resize(200, 200)
w2.move(320, 200)
lab = QLabel(w2)
pm = QPixmap(r"E:\RentAGirl\assets\chizuru_02.png").scaledToHeight(200, Qt.SmoothTransformation)
lab.setPixmap(pm)
lab.resize(pm.size())
w2.show()

QTimer.singleShot(4000, app.quit)
app.exec()
print("windows:", w1.geometry(), w2.geometry(), flush=True)
