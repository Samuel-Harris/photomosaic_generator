import sys
from PyQt5 import QtWidgets
import PhotomosaicGenerator
import GUI


def main():
    photomosaic_generator = PhotomosaicGenerator.PhotomosaicGenerator()
    app = QtWidgets.QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    gui = GUI.Window(photomosaic_generator)
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
