from MSE_tile_matcher import MSE_match_images
from K_means_clusterer import k_means_fit_images, k_means_find_cluster

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


class window(QMainWindow):

    def __init__(self, photomosaic_generator):
        self.photomosaic_generator = photomosaic_generator
        self.x_tiles = 10
        self.y_tiles = 10

        super(window, self).__init__()
        self.setGeometry(1000, 100, 500, 500)
        self.setWindowTitle('photomosaic generator')
        self.setWindowIcon(QIcon(r'..\img_assets\icon.png'))

        extractAction = QAction('&Quit', self)
        extractAction.setStatusTip('leave the app')
        extractAction.triggered.connect(self.close_application)

        self.statusBar()

        mainMenu = self.menuBar()
        fileMenu = mainMenu.addMenu('&File')
        fileMenu.addAction(extractAction)

        set_input_dir_btn = QAction(QIcon(r'..\img_assets\folder.png'), 'set input image directory', self)
        set_input_dir_btn.triggered.connect(self.set_input_dir)

        set_target_image_btn = QAction(QIcon(r'..\img_assets\landscape.png'), 'set target image', self)
        set_target_image_btn.triggered.connect(self.set_target_image)

        generate_photomosaic_btn = QAction(QIcon(r'..\img_assets\pixelated_landscape.png'), 'generate photomosaic',
                                           self)
        generate_photomosaic_btn.triggered.connect(self.generate_photomosaic)

        self.toolBar = self.addToolBar('Extraction')
        self.toolBar.addAction(set_input_dir_btn)
        self.toolBar.addAction(set_target_image_btn)
        self.toolBar.addAction(generate_photomosaic_btn)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.lay = QVBoxLayout(self.central_widget)

        label = QLabel(self)
        pixmap = QPixmap(r'C:/my_stuff/photomosaic_generator/target_image/target_image.jpg')
        label.setPixmap(pixmap)
        self.resize(pixmap.width(), pixmap.height())
        self.lay.addWidget(label)

        self.show()

    def close_application(self):
        print('whooo so custom')
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
        file_path, _ = QFileDialog.getOpenFileName(self, 'Select Target Image', '', 'Images (*.png *jpeg *jpg)', '..',
                                                   options=options)

        if file_path != '':
            self.photomosaic_generator.set_target_image(file_path)

    def generate_photomosaic(self):
        def thread_generate_photomosaic(photomosaic_generator):
            print('pre-processing target')
            photomosaic_generator.pre_process_target(self.x_tiles, self.y_tiles)

            print('pre-processing input')
            photomosaic_generator.pre_process_input(threads=7)

            print('fitting clusters')
            photomosaic_generator.fit_clusters(k_means_fit_images, k_means_find_cluster)

            print('setting image matcher')
            photomosaic_generator.set_image_matcher(MSE_match_images)

            print('matching tiles')
            photomosaic_generator.match_tiles()

            print('combining images')
            photomosaic_generator.combine_images()

            print('showing images')
            img = photomosaic_generator.get_image()
            print(img.shape)
            # height, width, channel = img.shape
            # bytesPerLine = 3 * width
            # qImg = QImage(img, width, height, bytesPerLine, QImage.Format_RGB888)
            # pixmap = QPixmap.fromImage(qImg)
            # label = QLabel(self)
            # label.setPixmap(pixmap)
            # self.lay.addWidget(label)

            label = QLabel(self)
            pixmap = QPixmap(r'C:/my_stuff/photomosaic_generator/target_image/target_image.jpg')
            label.setPixmap(pixmap)
            self.resize(pixmap.width(), pixmap.height())
            self.lay.addWidget(label)

            self.show()
            print('image shown')

        t = threading.Thread(target=thread_generate_photomosaic, args=(self.photomosaic_generator,), daemon=True)
        t.start()


def run(photomosaic_generator):
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    Gui = window(photomosaic_generator)
    sys.exit(app.exec_())
