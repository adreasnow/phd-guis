from PyQt6 import uic
from PyQt6.QtWidgets import QMainWindow, QDialog
import pathlib

class Ui(QMainWindow):
    def __init__(self):
        super(Ui, self).__init__()
        uic.loadUi(f'{pathlib.Path(__file__).parent.resolve()}/../spectraView.ui', self)
        self.show()

class SaveLifetimeWindow(QDialog):
    def __init__(self):
        super().__init__()
        uic.loadUi(f'{pathlib.Path(__file__).parent.resolve()}/../saveLifetime.ui', self)
        # self.setModal(True)

class SaveSpectrumWindow(QDialog):
    def __init__(self):
        super().__init__()
        uic.loadUi(f'{pathlib.Path(__file__).parent.resolve()}/../saveSpectra.ui', self)
        # self.setModal(True)

class PrintDSWindow(QDialog):
    def __init__(self):
        super().__init__()
        uic.loadUi(f'{pathlib.Path(__file__).parent.resolve()}/../printDS.ui', self)
        # self.setModal(True)