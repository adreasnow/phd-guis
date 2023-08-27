from PyQt6 import uic
from PyQt6.QtWidgets import QMainWindow
import pathlib

class Ui(QMainWindow):
    def __init__(self) -> None:
        super(Ui, self).__init__()
        uic.loadUi(f'{pathlib.Path(__file__).parent.resolve()}/../spectraImport.ui', self)
        self.show()
