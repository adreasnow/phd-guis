from PyQt6 import uic
from PyQt6.QtWidgets import QMainWindow, QDialog
import pathlib

class Ui(QMainWindow):
    def __init__(self):
        super(Ui, self).__init__()
        uic.loadUi(f'{pathlib.Path(__file__).parent.resolve()}/../manageDS.ui', self)
        self.show()

class ResetWindow(QDialog):
    def __init__(self):
        super().__init__()
        uic.loadUi(f'{pathlib.Path(__file__).parent.resolve()}/../resetDS.ui', self)
        self.setModal(True)
