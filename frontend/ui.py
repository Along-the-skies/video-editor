import sys
import ctypes
from PySide6.QtCore import QUrl
from PySide6.QtWidgets import QApplication, QMainWindow, QFrame, QVBoxLayout, QWidget
from PySide6.QtWebEngineWidgets import QWebEngineView

class VideoMakerWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Video Maker")
        self.resize(1200, 800)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #faf9f5;
            }
        """)

        central = QWidget()
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        line = QFrame()
        line.setFixedHeight(1)
        line.setStyleSheet("background-color: #141414; border: none;")
        layout.addWidget(line)

        self.browser = QWebEngineView()
        self.browser.setUrl(QUrl("http://127.0.0.1:8000/"))
        layout.addWidget(self.browser)

        self.setCentralWidget(central)
        self.apply_titlebar_color()

    def apply_titlebar_color(self):
        hwnd = int(self.winId())
        color = 0xE1E7E9
        DWMWA_CAPTION_COLOR = 35
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd,
            DWMWA_CAPTION_COLOR,
            ctypes.byref(ctypes.c_int(color)),
            ctypes.sizeof(ctypes.c_int)
        )

def initialize_ui():
    app = QApplication(sys.argv)
    window = VideoMakerWindow()
    window.show()
    sys.exit(app.exec())