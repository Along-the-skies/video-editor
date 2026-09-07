import sys
import requests

from PySide6.QtCore import QUrl
from PySide6.QtWidgets import QApplication, QMainWindow, QMessageBox
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEngineProfile


class VideoMakerWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("VFRAME")
        self.resize(1200, 800)

        self.setStyleSheet("""
            QMainWindow {
                background-color: #faf9f5;
            }
        """)

        self.browser = QWebEngineView()
        self.setCentralWidget(self.browser)

        profile = self.browser.page().profile()
        profile.downloadRequested.connect(self.handle_download)

        self.browser.setUrl(QUrl("http://127.0.0.1:8000/"))

    def handle_download(self, download):
        download.accept()
        download.isFinishedChanged.connect(lambda: self.on_download_finished(download))

    def on_download_finished(self, download):
        if download.isFinished():
            path = download.downloadDirectory() + "/" + download.downloadFileName()
            QMessageBox.information(self, "Download complete", f"Your video was saved to:\n{path}")

    def closeEvent(self, event):
        try:
            resp = requests.get("http://127.0.0.1:8000/current_session", timeout=5)
            session_id = resp.json()
        except requests.RequestException as e:
            print("GET ERROR:", e)
            session_id = ""

        print(session_id)

        if session_id:
            try:
                response = requests.delete(
                    f"http://127.0.0.1:8000/session/{session_id}",
                    timeout=5
                )
                print("DELETE:", response.status_code, response.text)
            except requests.RequestException as e:
                print("DELETE ERROR:", e)

        event.accept()


def initialize_ui():
    app = QApplication(sys.argv)

    window = VideoMakerWindow()
    window.show()

    sys.exit(app.exec())