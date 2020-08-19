import threading
import sys
from PyQt5 import QtGui, QtWidgets
from PyQt5.QtCore import pyqtSignal, pyqtSlot, Qt
from PhotomosaicGenerator import MissingComponentError
from ProgressWindow import ProgressWindow


class Window(QtWidgets.QMainWindow):
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
        self.setWindowIcon(QtGui.QIcon(r'..\img_assets\icon.png'))
        self.toolBar = self.addToolBar('Extraction')

        self.x_tiles_spin_box = QtWidgets.QSpinBox()
        self.x_tiles_spin_box.setRange(1, sys.maxsize)
        self.x_tiles_spin_box.setValue(100)
        self.x_tiles_spin_box.setPrefix('column count: ')
        self.toolBar.addWidget(self.x_tiles_spin_box)

        self.y_tiles_spin_box = QtWidgets.QSpinBox()
        self.y_tiles_spin_box.setRange(1, sys.maxsize)
        self.y_tiles_spin_box.setValue(100)
        self.y_tiles_spin_box.setPrefix('row count: ')
        self.toolBar.addWidget(self.y_tiles_spin_box)

        set_input_dir_btn = QtWidgets.QAction(QtGui.QIcon(r'..\img_assets\folder.png'), 'set input image directory', self)
        set_input_dir_btn.triggered.connect(self.set_input_dir)
        self.toolBar.addAction(set_input_dir_btn)

        set_target_image_btn = QtWidgets.QAction(QtGui.QIcon(r'..\img_assets\landscape.png'), 'set target image', self)
        set_target_image_btn.triggered.connect(self.set_target_image)
        self.toolBar.addAction(set_target_image_btn)

        generate_photomosaic_btn = QtWidgets.QAction(QtGui.QIcon(r'..\img_assets\pixelated_landscape.png'), 'generate photomosaic', self)
        generate_photomosaic_btn.triggered.connect(self.generate_photomosaic)
        self.toolBar.addAction(generate_photomosaic_btn)

        save_photomosaic_btn = QtWidgets.QAction(QtGui.QIcon(r'..\img_assets\save_icon.png'), 'save photomosaic', self)
        save_photomosaic_btn.triggered.connect(self.save_photomosaic)
        self.toolBar.addAction(save_photomosaic_btn)

        self.central_widget = QtWidgets.QWidget()
        self.setCentralWidget(self.central_widget)
        self.lay = QtWidgets.QVBoxLayout(self.central_widget)

        self.image = QtWidgets.QLabel(self)
        pixmap = QtGui.QPixmap(r'..\img_assets\default_image.jpg').scaled(800, 800, Qt.KeepAspectRatio)
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
        if not self.generating:
            options = QtWidgets.QFileDialog.Options()
            options |= QtWidgets.QFileDialog.DontUseNativeDialog
            options |= QtWidgets.QFileDialog.ShowDirsOnly
            file_dir = QtWidgets.QFileDialog.getExistingDirectory(self, 'Select Input Image Directory', '..', options=options)

            self.photomosaic_generator.set_input_directory_path(file_dir)
        else:
            error_msg_box = QtWidgets.QMessageBox.critical(self, 'Error', 'Image is already being generated. Please wait until it has finished to select another input image directory.')

    def set_target_image(self):
        if not self.generating:
            options = QtWidgets.QFileDialog.Options()
            options |= QtWidgets.QFileDialog.DontUseNativeDialog
            file_path, _ = QtWidgets.QFileDialog.getOpenFileName(self, 'Select Target Image', '..', 'Images (*jpg *.png)', '..',
                                                       options=options)

            if file_path != '':
                self.photomosaic_generator.set_target_image(file_path)

                img = self.photomosaic_generator.get_target_image()
                height, width, channel = img.shape
                bytesPerLine = 3 * width
                qImg = QtGui.QImage(img, width, height, bytesPerLine, QtGui.QImage.Format_RGB888)
                pixmap = QtGui.QPixmap.fromImage(qImg).scaled(800, 800, Qt.KeepAspectRatio)
                self.image.setPixmap(pixmap)
                self.resize(pixmap.width(), pixmap.height())
        else:
            error_msg_box = QtWidgets.QMessageBox.critical(self, 'Error', 'Image is already being generated. Please wait until it has finished to select another target image.')

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
        error_msg_box = QtWidgets.QMessageBox.critical(self, 'Error', self.error_msg)

    def generate_photomosaic(self):
        @pyqtSlot()
        def thread_generate_photomosaic():
            try:
                self.preprocessing_images_started.emit()
                self.photomosaic_generator.pre_process_images(self.x_tiles_spin_box.value(), self.y_tiles_spin_box.value())

                self.tile_matching_started.emit()
                self.photomosaic_generator.generate_photomosaic()

                img = self.photomosaic_generator.get_output_image()

                height, width, channel = img.shape
                bytesPerLine = 3 * width
                qImg = QtGui.QImage(img, width, height, bytesPerLine, QtGui.QImage.Format_RGB888)
                pixmap = QtGui.QPixmap.fromImage(qImg).scaled(800, 800, Qt.KeepAspectRatio)
                self.image.setPixmap(pixmap)
                self.resize(pixmap.width(), pixmap.height())

                self.generating_photomosaic_finished.emit()
                self.show()
            except MemoryError as e:
                self.error_msg = 'Too much memory used. Try increasing the row/column count, removing some images from the input directory, or reducing the size of the target image.'
                self.exception_raised.emit()
            except Exception as e:
                self.error_msg = str(e)
                self.exception_raised.emit()
            finally:
                self.generating_photomosaic_finished.emit()
                self.generating = False

        if not self.generating:
            try:
                self.photomosaic_generator.can_generate_photomosaic()
            except MissingComponentError as error_msg:
                error_msg_box = QtWidgets.QMessageBox.critical(self, 'Error', str(error_msg))
            else:
                self.generating = True
                self.error_msg = None

                self.progress_window.show()
                t = threading.Thread(target=thread_generate_photomosaic, daemon=True)
                t.start()
        else:
            error_msg_box = QtWidgets.QMessageBox.critical(self, 'Error',
                                                 'Image is already being generated. Please wait until it has finished to start generating another one.')

    def save_photomosaic(self):
        try:
            self.photomosaic_generator.can_save_image()
            if self.generating:
                raise MissingComponentError('Cannot save. Image is currently being generated.')
        except MissingComponentError as error_msg:
            error_msg_box = QtWidgets.QMessageBox.critical(self, 'Error', str(error_msg))
            return

        options = QtWidgets.QFileDialog.Options()
        options |= QtWidgets.QFileDialog.DontUseNativeDialog
        file_name, file_type = QtWidgets.QFileDialog.getSaveFileName(self, 'Save photomosaic', '..', 'jpg (*.jpg);;png (*.png)',
                                                           '..', options=options)
        file_type = file_type[-5:-1]
        if file_name != '':
            self.photomosaic_generator.save_image(file_name + file_type if file_name[-4:] != file_type else file_name)
