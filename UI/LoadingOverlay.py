from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QMovie

class LoadingOverlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setStyleSheet("background-color: rgba(0, 0, 0, 120);")  # semi-transparent gray

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.label = QLabel("Loading...")
        self.label.setStyleSheet("color: white; font-size: 16px;")
        layout.addWidget(self.label)

        # Optional: animated GIF spinner
        self.spinner = QLabel()
        movie = QMovie("spinner.gif")  # put a small spinner GIF in your project
        self.spinner.setMovie(movie)
        movie.start()
        layout.addWidget(self.spinner)

        self.hide()

    def show_overlay(self):
        self.resize(self.parent().size())
        self.show()

    def hide_overlay(self):
        self.hide()