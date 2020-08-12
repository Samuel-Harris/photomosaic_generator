from PyQt5 import QtCore, QtWidgets

import numpy as np
import os
import time
import threading
import sys
from skimage import io
from PyQt5.QtCore import QCoreApplication, Qt
from PyQt5.QtGui import QIcon, QColor, QImage, QPixmap
from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow, QPushButton, QAction, QMessageBox
from PyQt5.QtWidgets import QCalendarWidget, QFontDialog, QColorDialog, QTextEdit, QFileDialog, QVBoxLayout
from PyQt5.QtWidgets import QCheckBox, QProgressBar, QComboBox, QLabel, QStyleFactory, QLineEdit, QInputDialog
from PhotomosaicGenerator import MissingComponentError


class window(QMainWindow):

    def __init__(self, photomosaic_generator):
        self.photomosaic_generator = photomosaic_generator
        self.x_tiles = 100
        self.y_tiles = 100

        super(window, self).__init__()
        self.setGeometry(1000, 100, 500, 500)
        self.setWindowTitle('photomosaic generator')
        self.setWindowIcon(QIcon(r'..\img_assets\icon.png'))

        set_input_dir_btn = QAction(QIcon(r'..\img_assets\folder.png'), 'set input image directory', self)
        set_input_dir_btn.triggered.connect(self.set_input_dir)

        set_target_image_btn = QAction(QIcon(r'..\img_assets\landscape.png'), 'set target image', self)
        set_target_image_btn.triggered.connect(self.set_target_image)

        generate_photomosaic_btn = QAction(QIcon(r'..\img_assets\pixelated_landscape.png'), 'generate photomosaic',
                                           self)
        generate_photomosaic_btn.triggered.connect(self.generate_photomosaic)

        save_photomosaic_btn = QAction(QIcon(r'..\img_assets\save_icon.png'), 'generate photomosaic', self)
        save_photomosaic_btn.triggered.connect(self.save_photomosaic)

        self.toolBar = self.addToolBar('Extraction')
        self.toolBar.addAction(set_input_dir_btn)
        self.toolBar.addAction(set_target_image_btn)
        self.toolBar.addAction(generate_photomosaic_btn)
        self.toolBar.addAction(save_photomosaic_btn)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.lay = QVBoxLayout(self.central_widget)

        self.image = QLabel(self)
        pixmap = QPixmap(r'..\img_assets\default_image.jpg').scaled(800, 800, QtCore.Qt.KeepAspectRatio)
        self.image.setPixmap(pixmap)
        self.lay.addWidget(self.image)

        self.show()

        self.error_msg = None

    def closeEvent(self, event):
        sys.exit()

    def set_input_dir(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        options |= QFileDialog.ShowDirsOnly
        file_dir = QFileDialog.getExistingDirectory(self, 'Select Input Image Directory', '..', options=options)

        self.photomosaic_generator.set_input_directory_path(file_dir)

    def set_target_image(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        file_path, _ = QFileDialog.getOpenFileName(self, 'Select Target Image', '..', 'Images (*jpg *.png)', '..',
                                                   options=options)

        if file_path != '':
            self.photomosaic_generator.set_target_image(file_path)

            img = self.photomosaic_generator.get_target_image()
            if img.dtype == np.float64:
                img *= 255
                img = img.astype('int8')
            height, width, channel = img.shape
            bytesPerLine = 3 * width
            qImg = QImage(img, width, height, bytesPerLine, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(qImg).scaled(800, 800, QtCore.Qt.KeepAspectRatio)
            self.image.setPixmap(pixmap)
            self.resize(pixmap.width(), pixmap.height())

    def generate_photomosaic(self):
        def thread_generate_photomosaic(photomosaic_generator):
            start = time.time()
            try:
                photomosaic_generator.generate_image()
            except MissingComponentError as msg:
                self.error_msg = msg
                return

            img = photomosaic_generator.get_image()

            img *= 255
            img = img.astype('int8')
            height, width, channel = img.shape
            bytesPerLine = 3 * width
            qImg = QImage(img, width, height, bytesPerLine, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(qImg).scaled(800, 800, QtCore.Qt.KeepAspectRatio)
            self.image.setPixmap(pixmap)
            self.resize(pixmap.width(), pixmap.height())

            self.show()
            print('image shown')

            end = time.time()
            print('time: ' + str(end - start) + 's')

        self.error_msg = None
        t = threading.Thread(target=thread_generate_photomosaic, args=(self.photomosaic_generator,), daemon=True)
        t.start()
        if self.error_msg is not None:
            error_msg_box = QMessageBox.critical(self, 'Error', str(self.error_msg))

    def save_photomosaic(self):
        error_msg = self.photomosaic_generator.can_save_image()
        if error_msg is None:
            options = QFileDialog.Options()
            options |= QFileDialog.DontUseNativeDialog
            file_name, file_type = QFileDialog.getSaveFileName(self, 'Save photomosaic', '', 'jpg (*.jpg);;png (*.png)',
                                                          '..', options=options)
            file_type = file_type[-5:-1]
            self.photomosaic_generator.save_image(file_name + file_type if file_name[-4:] != file_type else file_name)
        else:
            error_msg_box = QMessageBox.critical(self, 'Error', error_msg)


def run(photomosaic_generator):
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    Gui = window(photomosaic_generator)
    sys.exit(app.exec_())
