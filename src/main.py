import sys
from PyQt5 import QtWidgets
import PhotomosaicGenerator
import GUI


def main():
    """Instantiates the PhotomosaicGenerator and runs the GUI."""
    photomosaic_generator = PhotomosaicGenerator.PhotomosaicGenerator()
    app = QtWidgets.QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    gui = GUI.Window(photomosaic_generator)
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
