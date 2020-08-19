import numpy as np
import os
import time
import threading
import sys
from skimage import io
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import pyqtSignal, pyqtSlot, QObject, Qt, QThread, QTimer
from PyQt5.QtGui import QIcon, QColor, QImage, QPixmap
from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow, QPushButton, QAction, QMessageBox, QSpinBox
from PyQt5.QtWidgets import QCalendarWidget, QFontDialog, QColorDialog, QTextEdit, QFileDialog, QVBoxLayout
from PyQt5.QtWidgets import QCheckBox, QProgressBar, QComboBox, QLabel, QStyleFactory, QLineEdit, QInputDialog

from PhotomosaicGenerator import MissingComponentError
from ProgressWindow import ProgressWindow


class Window(QMainWindow):
    preprocessing_images_started = pyqtSignal()
    tile_matching_started = pyqtSignal()
    generating_photomosaic_finished = pyqtSignal()
    exception_raised = pyqtSignal()

    def __init__(self, photomosaic_generator):
        self.photomosaic_generator = photomosaic_generator
        self.progress_window = ProgressWindow()
        self.error_msg = None
        self.generating = False

        super(Window, self).__init__()
        self.setGeometry(1000, 100, 500, 500)
        self.setWindowTitle('photomosaic generator')
        self.setWindowIcon(QIcon(r'..\img_assets\icon.png'))
        self.toolBar = self.addToolBar('Extraction')

        self.x_tiles_spin_box = QSpinBox()
        self.x_tiles_spin_box.setRange(1, sys.maxsize)
        self.x_tiles_spin_box.setValue(100)
        self.x_tiles_spin_box.setPrefix('column count: ')
        self.toolBar.addWidget(self.x_tiles_spin_box)

        self.y_tiles_spin_box = QSpinBox()
        self.y_tiles_spin_box.setRange(1, sys.maxsize)
        self.y_tiles_spin_box.setValue(100)
        self.y_tiles_spin_box.setPrefix('row count: ')
        self.toolBar.addWidget(self.y_tiles_spin_box)

        set_input_dir_btn = QAction(QIcon(r'..\img_assets\folder.png'), 'set input image directory', self)
        set_input_dir_btn.triggered.connect(self.set_input_dir)
        self.toolBar.addAction(set_input_dir_btn)

        set_target_image_btn = QAction(QIcon(r'..\img_assets\landscape.png'), 'set target image', self)
        set_target_image_btn.triggered.connect(self.set_target_image)
        self.toolBar.addAction(set_target_image_btn)

        generate_photomosaic_btn = QAction(QIcon(r'..\img_assets\pixelated_landscape.png'), 'generate photomosaic', self)
        generate_photomosaic_btn.triggered.connect(self.generate_photomosaic)
        self.toolBar.addAction(generate_photomosaic_btn)

        save_photomosaic_btn = QAction(QIcon(r'..\img_assets\save_icon.png'), 'save photomosaic', self)
        save_photomosaic_btn.triggered.connect(self.save_photomosaic)
        self.toolBar.addAction(save_photomosaic_btn)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.lay = QVBoxLayout(self.central_widget)

        self.image = QLabel(self)
        pixmap = QPixmap(r'..\img_assets\default_image.jpg').scaled(800, 800, QtCore.Qt.KeepAspectRatio)
        self.image.setPixmap(pixmap)
        self.lay.addWidget(self.image)

        self.show()

        self.preprocessing_images_started.connect(self.on_preprocessing_images_started)
        self.tile_matching_started.connect(self.on_tile_matching_started)
        self.generating_photomosaic_finished.connect(self.on_generating_photomosaic_finished)
        self.exception_raised.connect(self.on_exception_raised)

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
            height, width, channel = img.shape
            bytesPerLine = 3 * width
            qImg = QImage(img, width, height, bytesPerLine, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(qImg).scaled(800, 800, QtCore.Qt.KeepAspectRatio)
            self.image.setPixmap(pixmap)
            self.resize(pixmap.width(), pixmap.height())

    @pyqtSlot()
    def on_preprocessing_images_started(self):
        self.progress_window.show_pre_process_images_animation()

    @pyqtSlot()
    def on_tile_matching_started(self):
        self.progress_window.show_tile_matching_animation()

    @pyqtSlot()
    def on_generating_photomosaic_finished(self):
        self.progress_window.hide()

    @pyqtSlot()
    def on_exception_raised(self):
        error_msg_box = QMessageBox.critical(self, 'Error', self.error_msg)

    def generate_photomosaic(self):
        @pyqtSlot()
        def thread_generate_photomosaic():
            try:
                start = time.time()
                self.preprocessing_images_started.emit()
                self.photomosaic_generator.pre_process_target(self.x_tiles_spin_box.value(), self.y_tiles_spin_box.value())
                self.photomosaic_generator.pre_process_input(threads=7)
                self.photomosaic_generator.fit_clusters()

                self.tile_matching_started.emit()
                self.photomosaic_generator.match_tiles()
                self.photomosaic_generator.combine_images()

                img = self.photomosaic_generator.get_image()

                height, width, channel = img.shape
                bytesPerLine = 3 * width
                qImg = QImage(img, width, height, bytesPerLine, QImage.Format_RGB888)
                pixmap = QPixmap.fromImage(qImg).scaled(800, 800, QtCore.Qt.KeepAspectRatio)
                self.image.setPixmap(pixmap)
                self.resize(pixmap.width(), pixmap.height())

                self.generating_photomosaic_finished.emit()
                self.show()

                end = time.time()
                print('time: ' + str(end - start) + 's')
            except Exception as e:
                self.error_msg = str(e)
                self.exception_raised.emit()
            finally:
                self.generating_photomosaic_finished.emit()
                self.generating = False

        if not self.generating:
            try:
                self.photomosaic_generator.can_generate_image()
            except MissingComponentError as error_msg:
                error_msg_box = QMessageBox.critical(self, 'Error', str(error_msg))
            else:
                self.generating = True
                self.error_msg = None

                self.progress_window.show()
                t = threading.Thread(target=thread_generate_photomosaic, daemon=True)
                t.start()
        else:
            error_msg_box = QMessageBox.critical(self, 'Error',
                                                 'Image is already being generated. Please wait until it has finished to start generating another one')

    def save_photomosaic(self):
        try:
            self.photomosaic_generator.can_save_image()
            if self.generating:
                raise MissingComponentError('Cannot save. Image is currently being generated.')
        except MissingComponentError as error_msg:
            error_msg_box = QMessageBox.critical(self, 'Error', str(error_msg))
            return

        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        file_name, file_type = QFileDialog.getSaveFileName(self, 'Save photomosaic', '..', 'jpg (*.jpg);;png (*.png)',
                                                           '..', options=options)
        file_type = file_type[-5:-1]
        if file_name != '':
            self.photomosaic_generator.save_image(file_name + file_type if file_name[-4:] != file_type else file_name)


def run(photomosaic_generator):
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    Gui = Window(photomosaic_generator)
    sys.exit(app.exec_())
