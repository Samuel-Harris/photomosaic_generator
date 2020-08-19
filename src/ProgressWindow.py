from PyQt5 import QtGui, QtWidgets
from PyQt5.QtCore import Qt


class ProgressWindow(QtWidgets.QWidget):
    """A class for the window that shows the progress of the photomosaic generation.

    :method __init__: initialises the ProgressWindow variables
    :method show_pre_process_images_animation: shows the pre-processing images animation on the progress window
    :method show_tile_matching_animation: shows the tile matching animation on the progress window
    """

    def __init__(self):
        """Initialises the ProgressWindow variables"""

        super().__init__()

        self.setGeometry(30, 40, 400, 200)
        self.setWindowTitle('generating image')
        self.setWindowIcon(QtGui.QIcon(r'..\img_assets\icon.png'))

        self.setLayout(QtWidgets.QVBoxLayout())
        self._layout = self.layout()

        self._gif = QtWidgets.QLabel()
        movie = QtGui.QMovie(r'..\img_assets\pre_process_images_animation.gif')
        self._gif.setMovie(movie)
        movie.start()
        self._layout.addWidget(self._gif)

        self._message = QtWidgets.QLabel()
        self._message.setText('pre-processing images')
        self._message.setAlignment(Qt.AlignCenter)
        self._layout.addWidget(self._message)

        self.setWindowFlag(Qt.WindowCloseButtonHint, False)

    def show_pre_process_images_animation(self):
        """Shows the pre-processing images animation on the progress window."""

        movie = QtGui.QMovie(r'..\img_assets\pre_process_images_animation.gif')
        self._gif.setMovie(movie)
        movie.start()

        self._message.setText('pre-processing images')

    def show_tile_matching_animation(self):
        """Shows the tile matching animation on the progress window."""

        movie = QtGui.QMovie(r'..\img_assets\matching_tiles_animation.gif')
        self._gif.setMovie(movie)
        movie.start()

        self._message.setText('matching tiles')
