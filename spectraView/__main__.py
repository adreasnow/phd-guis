import sys
import resources as r
import pandas as pd
import matplotlib.pyplot as plt
from PyQt6 import QtWidgets
from functools import partial
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from .funcs.guiFuncs import add_items_combo, add_items_list, setup_QRangeSlider
from .funcs.lifetimeFuncs import loadFLSpectrum, loadFromDSFL, saveToDSFL
from .funcs.spectraFuncs import loadSpectrum, loadFromDS, saveToDS, saveToDS_reset
from .funcs.classes import Ui, SaveLifetimeWindow, SaveSpectrumWindow, PrintDSWindow
from .funcs.rateLimited import *
import qtawesome as qta

def extractIndices(df: pd.DataFrame) -> list[float]:
    levels = len(df.index[0])
    indexLists = [[] for i in range(levels)]
    for row in df.index:
        for count, level in enumerate(row):
            if level not in indexLists[count]:
                indexLists[count] += [level]
    return [df.columns.to_list()] + indexLists

def init_spectra_plot(ui: Ui) -> None:
    ui.verticalLayout_spectra = QtWidgets.QVBoxLayout(ui.groupBox_spectra)
    ui.verticalLayout_spectra.setObjectName("verticalLayout_spectra")
    ui.figure_spectra, ui.ax_spectra = plt.subplots(1, 1)
    ui.canvas_spectra = FigureCanvas(ui.figure_spectra)
    ui.toolbar_spectra = NavigationToolbar(ui.canvas_spectra, ui)
    ui.verticalLayout_spectra.addWidget(ui.toolbar_spectra)
    ui.verticalLayout_spectra.addWidget(ui.canvas_spectra)

def init_lifetime_plot(ui: Ui) -> None:
    ui.verticalLayout_lifetime = QtWidgets.QVBoxLayout(ui.groupBox_lifetime)
    ui.verticalLayout_lifetime.setObjectName("verticalLayout_lifetime")
    ui.figure_lifetime, ui.ax_lifetime = plt.subplots(1, 1)
    ui.canvas_lifetime = FigureCanvas(ui.figure_lifetime)
    ui.toolbar_lifetime = NavigationToolbar(ui.canvas_lifetime, ui)
    ui.verticalLayout_lifetime.addWidget(ui.toolbar_lifetime)
    ui.verticalLayout_lifetime.addWidget(ui.canvas_lifetime)

def save_lifetime_window(ui: Ui) -> None:
    ui.saveLifetimeWindow = SaveLifetimeWindow()
    with r.statusLoad(df='spectra') as df:
        solvents, fluorophores, spectra = extractIndices(df)
    add_items_combo(ui.saveLifetimeWindow.fluorophore, fluorophores)
    add_items_combo(ui.saveLifetimeWindow.solvent, [i for i in solvents if i != r.Solvents.gas])

    ui.saveLifetimeWindow.load_button.clicked.connect(partial(loadFromDSFL, ui))
    ui.saveLifetimeWindow.save_button.clicked.connect(partial(saveToDSFL, ui))
    ui.saveLifetimeWindow.show()

def save_spectrum_window(ui: Ui) -> None:
    ui.saveSpectrumWindow = SaveSpectrumWindow()
    with r.statusLoad(df='spectra') as df:
        solvents, fluorophores, spectra = extractIndices(df)
    add_items_combo(ui.saveSpectrumWindow.fluorophore, fluorophores)
    add_items_combo(ui.saveSpectrumWindow.solvent, [i for i in solvents if i != r.Solvents.gas])

    ui.saveSpectrumWindow.load_button.clicked.connect(partial(loadFromDS, ui))
    ui.saveSpectrumWindow.save_button.clicked.connect(partial(saveToDS, ui))
    ui.saveSpectrumWindow.reset_button.clicked.connect(partial(saveToDS_reset, ui))
    ui.saveSpectrumWindow.show()

def print_ds(ui: Ui) -> None:
    ui.dsWindow = PrintDSWindow()
    with r.statusLoad('dataset') as df:
        dfOut = df.style.applymap(lambda x: 'color : blue' if (x not in [None, 0.00]) or (pd.isna(x)) else 'color : red').format(precision=3).to_html()

    with r.statusLoad('spectra') as df:
        dfOut += df.notnull().style.applymap(lambda x: 'color : blue' if x else 'color : red').to_html()

    ui.dsWindow.dsOut.setHtml(dfOut)
    ui.dsWindow.show()
    return

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    app.setWindowIcon(qta.icon('fa5s.chart-area'))
    ui = Ui()
    
    with r.statusLoad(df='spectra') as df:
        solvents, fluorophores, spectra = extractIndices(df)

    add_items_list(ui.fluorophoreList_widg, fluorophores)
    add_items_list(ui.solventList_widg, [i for i in solvents if i != r.Solvents.gas])
    add_items_list(ui.spectraList_widg, [i for i in spectra if i != r.spectraType.lifetime])
    setup_QRangeSlider(ui.fl_max_x, -20, 500, values=(-1, 20), output=(ui.fl_min_x_out, ui.fl_max_x_out))
    setup_QRangeSlider(ui.amp_range, 0, 50, values=(0, 50), output=(ui.amp_low, ui.amp_high), outscale=0.01)

    init_spectra_plot(ui)
    init_lifetime_plot(ui)

    ui.deriv.toggled.connect(partial(loadSpectrum, ui))
    ui.nonderiv.toggled.connect(partial(loadSpectrum, ui))
    ui.plotGauss.stateChanged.connect(partial(loadSpectrum, ui))
    ui.printGauss.stateChanged.connect(partial(loadSpectrum, ui))
    ui.printESD.stateChanged.connect(partial(loadSpectrum, ui))
    ui.printLMax.stateChanged.connect(partial(loadSpectrum, ui))
    ui.norm.currentIndexChanged.connect(partial(loadSpectrum, ui))
    ui.units.currentIndexChanged.connect(partial(loadSpectrum, ui))
    ui.amp_low.valueChanged.connect(partial(loadSpectrum, ui))
    ui.amp_high.valueChanged.connect(partial(loadSpectrum, ui))
    ui.esd_offset.valueChanged.connect(partial(loadSpectrum, ui))
    ui.fluorophoreList_widg.itemSelectionChanged.connect(partial(loadSpectrum, ui))
    ui.solventList_widg.itemSelectionChanged.connect(partial(loadSpectrum, ui))
    ui.spectraList_widg.itemSelectionChanged.connect(partial(loadSpectrum, ui))
    ui.savgol_level.valueChanged.connect(partial(loadSpectrum, ui))
    ui.savgol.stateChanged.connect(partial(loadSpectrum, ui))

    ui.fl_min_x_out.valueChanged.connect(partial(loadFLSpectrum, ui))
    ui.fl_max_x_out.valueChanged.connect(partial(loadFLSpectrum, ui))
    ui.plotData.stateChanged.connect(partial(loadFLSpectrum, ui))
    ui.printData.stateChanged.connect(partial(loadFLSpectrum, ui))
    ui.verbosePrint.stateChanged.connect(partial(loadFLSpectrum, ui))
    ui.scale.stateChanged.connect(partial(loadFLSpectrum, ui))
    ui.logPlot.stateChanged.connect(partial(loadFLSpectrum, ui))
    ui.fluorophoreList_widg.itemSelectionChanged.connect(partial(loadFLSpectrum, ui))
    ui.solventList_widg.itemSelectionChanged.connect(partial(loadFLSpectrum, ui))
    ui.spectraList_widg.itemSelectionChanged.connect(partial(loadFLSpectrum, ui))

    ui.save_lifetime_button.clicked.connect(partial(save_lifetime_window, ui))
    ui.save_spectrum_button.clicked.connect(partial(save_spectrum_window, ui))

    ui.print_button.clicked.connect(partial(print_ds, ui))

    setup_df()

    sys.exit(app.exec())
