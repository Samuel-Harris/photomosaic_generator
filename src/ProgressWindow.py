import sys
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtGui import QIcon, QColor, QImage, QPixmap
from PyQt5.QtWidgets import QWidget, QProgressBar, QPushButton, QApplication
from PyQt5.QtWidgets import QCalendarWidget, QFontDialog, QColorDialog, QTextEdit, QFileDialog, QVBoxLayout
from PyQt5.QtWidgets import QCheckBox, QProgressBar, QComboBox, QLabel, QStyleFactory, QLineEdit, QInputDialog
from PyQt5.QtCore import QBasicTimer, Qt
from PyQt5.QtGui import QMovie


class ProgressWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setGeometry(30, 40, 400, 200)
        self.setWindowTitle('generating image')
        self.setWindowIcon(QIcon(r'..\img_assets\icon.png'))

        self.setLayout(QtWidgets.QVBoxLayout())
        self._layout = self.layout()

        self._gif = QtWidgets.QLabel()
        movie = QMovie(r'..\img_assets\pre_process_images_animation.gif')
        self._gif.setMovie(movie)
        movie.start()
        self._layout.addWidget(self._gif)

        self._message = QtWidgets.QLabel()
        self._message.setText('pre-processing images')
        self._message.setAlignment(Qt.AlignCenter)
        self._layout.addWidget(self._message)

        self.setWindowFlag(Qt.WindowCloseButtonHint, False)

    def show_pre_process_images_animation(self):
        movie = QMovie(r'..\img_assets\pre_process_images_animation.gif')
        self._gif.setMovie(movie)
        movie.start()

        self._message.setText('pre-processing images')

    def show_tile_matching_animation(self):
        movie = QMovie(r'..\img_assets\matching_tiles_animation.gif')
        self._gif.setMovie(movie)
        movie.start()

        self._message.setText('matching tiles')