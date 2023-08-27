import sys
import resources as r
from PyQt6.QtWidgets import QApplication
from functools import partial
from .funcs.ui import Ui
from .funcs.generalFuncs import extractIndices
from .funcs.lifetimeFuncs import populate_fl, connect_fl, saveToDSFL, plotFL, fl_reset
from .funcs.esdFuncs import populate_esd, connect_esd, saveESD, processESD, esd_reset
from .funcs.spectraFuncs import populate_spectra, connect_spectra, saveSpectra, loadSpectra, spectra_reset
from .funcs.deconvFuncs import populate_deconv, connect_deconv, saveDeconv, deconv, reset_deconv
import qtawesome as qta

def save(ui: Ui) -> None:
    if ui.tabWidget.currentIndex() == 0:
        saveSpectra(ui)
    if ui.tabWidget.currentIndex() == 1:
        saveESD(ui)
    if ui.tabWidget.currentIndex() == 2:
        saveToDSFL(ui)
    if ui.tabWidget.currentIndex() == 3:
        saveDeconv(ui)

def action(ui: Ui) -> None:
    if ui.tabWidget.currentIndex() == 0:
        loadSpectra(ui)
    if ui.tabWidget.currentIndex() == 1:
        processESD(ui)
    if ui.tabWidget.currentIndex() == 2:
        plotFL(ui)
    if ui.tabWidget.currentIndex() == 3:
        deconv(ui)

def reset(ui: Ui) -> None:
    if ui.tabWidget.currentIndex() == 0:
        spectra_reset(ui)
    if ui.tabWidget.currentIndex() == 1:
        esd_reset(ui)
    if ui.tabWidget.currentIndex() == 2:
        fl_reset(ui)
    if ui.tabWidget.currentIndex() == 3:
        reset_deconv(ui)

def populate(ui: Ui) -> None:
    populate_fl(ui)
    populate_esd(ui)
    populate_spectra(ui)
    populate_deconv(ui)

def connect(ui: Ui) -> None:
    connect_fl(ui)
    connect_esd(ui)
    connect_spectra(ui)
    connect_deconv(ui)
    ui.actionSave.triggered.connect(partial(save, ui))
    ui.actionPull_the_Lever_Kronk.triggered.connect(partial(action, ui))
    ui.actionWRONG_LEVER.triggered.connect(partial(reset, ui))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setWindowIcon(qta.icon('fa5s.sliders-h'))
    ui = Ui()
    with r.statusLoad(df='spectra') as df:
        solvents, fluorophores, spectra = extractIndices(df)

    populate(ui)
    connect(ui)

    sys.exit(app.exec())
