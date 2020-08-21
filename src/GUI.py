import threading
import sys
from PyQt5 import QtGui, QtWidgets
from PyQt5.QtCore import pyqtSignal, pyqtSlot, Qt
from PhotomosaicGenerator import MissingComponentError
from ProgressWindow import ProgressWindow


class Window(QtWidgets.QMainWindow):
    """A class that contains the methods and attributes for a photomosaic GUI.

    :method closeEvent: closes the window
    """

    preprocessing_images_started = pyqtSignal()
    tile_matching_started = pyqtSignal()
    generating_photomosaic_finished = pyqtSignal()
    exception_raised = pyqtSignal()

    def __init__(self, photomosaic_generator):
        """Initialises the Window object's attributes."""

        self.photomosaic_generator = photomosaic_generator
        self.progress_window = ProgressWindow()
        self.error_msg = None
        self.generating = False

        super(Window, self).__init__()
        self.setGeometry(1000, 100, 500, 500)
        self.setWindowTitle('photomosaic generator')
        self.setWindowIcon(QtGui.QIcon(r'..\img_assets\icon.png'))
        self.toolBar = self.addToolBar('Extraction')

        # setting up column count spin box
        self.x_tiles_spin_box = QtWidgets.QSpinBox()
        self.x_tiles_spin_box.setRange(1, sys.maxsize)
        self.x_tiles_spin_box.setValue(100)
        self.x_tiles_spin_box.setPrefix('column count: ')
        self.toolBar.addWidget(self.x_tiles_spin_box)

        # setting up row count spin box
        self.y_tiles_spin_box = QtWidgets.QSpinBox()
        self.y_tiles_spin_box.setRange(1, sys.maxsize)
        self.y_tiles_spin_box.setValue(100)
        self.y_tiles_spin_box.setPrefix('row count: ')
        self.toolBar.addWidget(self.y_tiles_spin_box)

        # setting up set input directory button
        set_input_dir_btn = QtWidgets.QAction(QtGui.QIcon(r'..\img_assets\folder.png'), 'set input image directory',
                                              self)
        set_input_dir_btn.triggered.connect(self.__set_input_dir)
        self.toolBar.addAction(set_input_dir_btn)

        # setting up set target image button
        set_target_image_btn = QtWidgets.QAction(QtGui.QIcon(r'..\img_assets\landscape.png'), 'set target image', self)
        set_target_image_btn.triggered.connect(self.__set_target_image)
        self.toolBar.addAction(set_target_image_btn)

        # setting up generate photomosaic button
        generate_photomosaic_btn = QtWidgets.QAction(QtGui.QIcon(r'..\img_assets\pixelated_landscape.png'),
                                                     'generate photomosaic', self)
        generate_photomosaic_btn.triggered.connect(self.__generate_photomosaic)
        self.toolBar.addAction(generate_photomosaic_btn)

        # setting up save photomosaic
        save_photomosaic_btn = QtWidgets.QAction(QtGui.QIcon(r'..\img_assets\save_icon.png'), 'save photomosaic', self)
        save_photomosaic_btn.triggered.connect(self.__save_display_image)
        self.toolBar.addAction(save_photomosaic_btn)

        # setting up display image
        self.central_widget = QtWidgets.QWidget()
        self.setCentralWidget(self.central_widget)
        self.lay = QtWidgets.QVBoxLayout(self.central_widget)
        self.image = QtWidgets.QLabel(self)
        pixmap = QtGui.QPixmap(r'..\img_assets\default_image.jpg').scaled(800, 800, Qt.KeepAspectRatio)
        self.image.setPixmap(pixmap)
        self.lay.addWidget(self.image)

        # connecting signals to functions
        self.preprocessing_images_started.connect(self.__on_pre_processing_images_started)
        self.tile_matching_started.connect(self.__on_tile_matching_started)
        self.generating_photomosaic_finished.connect(self.__on_generating_photomosaic_finished)
        self.exception_raised.connect(self.__on_exception_raised)

        self.show()

    def closeEvent(self, event):
        """Event of closing the window."""

        sys.exit()

    def __set_input_dir(self):
        """Setting the input directory."""

        if not self.generating:
            options = QtWidgets.QFileDialog.Options()
            options |= QtWidgets.QFileDialog.DontUseNativeDialog
            options |= QtWidgets.QFileDialog.ShowDirsOnly
            file_dir = QtWidgets.QFileDialog.getExistingDirectory(self, 'Select Input Image Directory', '..',
                                                                  options=options)

            self.photomosaic_generator.set_input_directory_path(file_dir)
        else:
            error_msg_box = QtWidgets.QMessageBox.critical(self, 'Error', 'Image is already being generated. Please'
                                                                          ' wait until it has finished to select'
                                                                          ' another input image directory.')

    def __set_target_image(self):
        """setting the target image."""

        if not self.generating:
            options = QtWidgets.QFileDialog.Options()
            options |= QtWidgets.QFileDialog.DontUseNativeDialog
            file_path, _ = QtWidgets.QFileDialog.getOpenFileName(self, 'Select Target Image', '..',
                                                                 'Images (*jpg *.png)', '..', options=options)

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
            error_msg_box = QtWidgets.QMessageBox.critical(self, 'Error', 'Image is already being generated. Please'
                                                                          ' wait until it has finished to select'
                                                                          ' another target image.')

    @pyqtSlot()
    def __on_pre_processing_images_started(self):
        """Function to connect starting pre-processing images to starting the pre-processing image animation."""

        self.progress_window.show_pre_process_images_animation()

    @pyqtSlot()
    def __on_tile_matching_started(self):
        """Function to connect starting tile matching to starting the tile matching animation."""

        self.progress_window.show_tile_matching_animation()

    @pyqtSlot()
    def __on_generating_photomosaic_finished(self):
        """Function to connect finishing generating the photomosaic to hiding the animation window."""

        self.progress_window.hide()

    @pyqtSlot()
    def __on_exception_raised(self):
        """Function to connect exceptions being raised to error message windows being created."""

        error_msg_box = QtWidgets.QMessageBox.critical(self, 'Error', self.error_msg)

    def __generate_photomosaic(self):
        """Generates a photomosaic using a separate thread."""

        @pyqtSlot()
        def thread_generate_photomosaic():
            """Generates a photomosaic."""

            try:
                self.preprocessing_images_started.emit()
                self.photomosaic_generator.pre_process_images(self.x_tiles_spin_box.value(),
                                                              self.y_tiles_spin_box.value())

                self.tile_matching_started.emit()
                self.photomosaic_generator.generate_photomosaic()

                img = self.photomosaic_generator.get_output_image()

                # displaying photomosaic
                height, width, channel = img.shape
                bytesPerLine = 3 * width
                qImg = QtGui.QImage(img, width, height, bytesPerLine, QtGui.QImage.Format_RGB888)
                pixmap = QtGui.QPixmap.fromImage(qImg).scaled(800, 800, Qt.KeepAspectRatio)
                self.image.setPixmap(pixmap)
                self.resize(pixmap.width(), pixmap.height())

                self.generating_photomosaic_finished.emit()
                self.show()
            except MemoryError:
                self.error_msg = 'Too much memory used. Try increasing the row/column count, removing some images' \
                                 ' from the input directory, or reducing the size of the target image.'
                self.exception_raised.emit()
            except Exception as e:
                self.error_msg = str(e)
                self.exception_raised.emit()
            finally:
                self.generating_photomosaic_finished.emit()
                self.generating = False

        if self.generating:
            error_msg_box = QtWidgets.QMessageBox.critical(self, 'Error', 'Image is already being generated. Please'
                                                                          ' wait until it has finished to start'
                                                                          ' generating another one.')
        else:
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

    def __save_display_image(self):
        """Saves the displayed image."""

        try:
            self.photomosaic_generator.can_save_image()
            if self.generating:
                raise MissingComponentError('Cannot save. Image is currently being generated.')
        except MissingComponentError as error_msg:
            error_msg_box = QtWidgets.QMessageBox.critical(self, 'Error', str(error_msg))
        else:
            options = QtWidgets.QFileDialog.Options()
            options |= QtWidgets.QFileDialog.DontUseNativeDialog
            file_name, file_type = QtWidgets.QFileDialog.getSaveFileName(self, 'Save photomosaic', '..',
                                                                         'jpg (*.jpg);;png (*.png)', options=options)
            file_type = file_type[-5:-1]
            if file_name != '':
                self.photomosaic_generator.save_image(file_name + file_type if file_name[-4:] != file_type else
                                                      file_name)
