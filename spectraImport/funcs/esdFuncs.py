import resources as r
import numpy as np
import matplotlib.pyplot as plt
from functools import partial
from pathlib import Path
from scipy.ndimage import gaussian_filter1d
from PyQt6.QtWidgets import QMessageBox, QFileDialog, QVBoxLayout
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from .guiFuncs import add_items_combo, setup_QRangeSlider
from .generalFuncs import extractIndices
from .ui import Ui

def populate_esd(ui: Ui) -> None:
    init_esd_plot(ui)
    with r.statusLoad('spectra') as df:
        solvents, fluorophores, _ = extractIndices(df)
    add_items_combo(ui.esd_fluorophore, fluorophores)
    add_items_combo(ui.esd_solvent, solvents)
    setup_QRangeSlider(ui.esd_range, 140, 619, output=(ui.esd_range_min, ui.esd_range_max), outscale=0.01)

def connect_esd(ui: Ui) -> None:
    ui.esd_spectrum_button.clicked.connect(partial(esd_browse, ui))
    ui.esd_load.clicked.connect(partial(processESD, ui))
    ui.esd_save.clicked.connect(partial(saveESD, ui))
    ui.esd_reset.clicked.connect(partial(esd_reset, ui))

def init_esd_plot(ui: Ui) -> None:
    ui.esd_layout = QVBoxLayout(ui.esd_frame)
    ui.esd_layout.setObjectName("esd_layout")
    ui.esd_figure, (ui.esd_ax1, ui.esd_ax2) = plt.subplots(2, 1, figsize=(8, 6), sharex=True)
    ui.esd_ax2.invert_xaxis()
    ui.esd_canvas = FigureCanvas(ui.esd_figure)
    ui.esd_toolbar = NavigationToolbar(ui.esd_canvas, ui)
    ui.esd_layout.addWidget(ui.esd_toolbar)
    ui.esd_layout.addWidget(ui.esd_canvas)

def esd_reset(ui: Ui) -> None:
    ui.esd_spectrum_text.setText('')
    ui.esd_total.setChecked(True)
    ui.esd_fc.setChecked(False)
    ui.esd_ht.setChecked(False)
    ui.esd_range_min.setValue(1.4)
    ui.esd_range_max.setValue(6.19)
    ui.esd_smoothing.setValue(500)
    ui.esd_offset.setValue(25)
    ui.esd_output.setPlainText('')
    ui.esd_fluorophore.setCurrentIndex(0)
    ui.esd_solvent.setCurrentIndex(0)

def clear_fl_plot(ui: Ui) -> None:
    for axes in [ui.esd_ax1, ui.esd_ax2]:
        axes.cla()
        axes.autoscale_view()
        axes.relim()

def esd_browse(ui: Ui) -> None:
    file_dialog = QFileDialog()
    directory = '/Volumes/MonARCH/fluorophores/'
    if ui.esd_spectrum_text.text() != '':
        path = Path(ui.esd_spectrum_text.text())
        if path.exists:
            directory = path.parent.as_posix()
    ui.esd_spectrum_text.setText(file_dialog.getOpenFileName(directory=directory, filter="ORCA ESD Spectrum files (*.spectrum)")[0])

def saveESD(ui: Ui) -> None:
    fluorophore = ui.esd_fluorophore.currentData()
    solvent = ui.esd_solvent.currentData()
    with r.statusLoad('spectra') as df:
        solvents, fluorophores, spectra = extractIndices(df)
        if fluorophore in fluorophores and solvent in solvents:
            try:
                df.at[(fluorophore, ui.spectrumObject.spectraType), solvent] = ui.spectrumObject
            except NameError:
                QMessageBox(icon=QMessageBox.Icon.Critical, text='Spectrum object not built yet').exec()
                return
        else:
            QMessageBox(icon=QMessageBox.Icon.Critical, text=f'{fluorophore} in {solvent} isn\'t in the dataframe!').exec()
            return

        QMessageBox(icon=QMessageBox.Icon.Information, text=f'Saved {fluorophore} in {solvent} {ui.spectrumObject.spectraType}!').exec()

def loadESD(ui: Ui) -> tuple[list[float], list[float], list[float], list[float]]:
    energyList = []
    totalList = []
    fcList = []
    htList = []
    processRange = (ui.esd_range_min.value(), ui.esd_range_max.value())

    clear_fl_plot(ui)

    fl = ui.esd_spectrum_text.text()
    if fl == '':
        QMessageBox(icon=QMessageBox.Icon.Critical, text='Files not Loaded').exec()
    else:
        nameList = fl.split('/')[-1].split('.')[0].split('_')
        for name in nameList:
            for fluorophore in r.Fluorophores:
                if name.lower() == fluorophore.name:
                    index = ui.esd_fluorophore.findData(fluorophore)
                    ui.esd_fluorophore.setCurrentIndex(index)
                    break
            for solvent in r.Solvents:
                if name.lower() == solvent.name:
                    index = ui.esd_solvent.findData(solvent)
                    ui.esd_solvent.setCurrentIndex(index)
                    break

    with open(fl, 'r') as f:
        lines = f.readlines()[1:]

    for line in lines:
        splitline = line.split()
        if float(splitline[0]) > processRange[0] and float(splitline[0]) < processRange[1]:
            energyList += [float(splitline[0])]
            totalList += [float(splitline[1])]
            fcList += [float(splitline[2])]
            htList += [float(splitline[3])]

    return energyList, totalList, fcList, htList

def buildESDSpectrumObject(ui: Ui, x: list[float], yT: list[float], yFC: list[float], yHT: list[float], peaks: list[float], amps: list[float]) -> None:
    if '/s0/' in ui.esd_spectrum_text.text():
        spectrumType = r.spectraType.esdex
    elif '/s1/' in ui.esd_spectrum_text.text() or '/s2/' in ui.esd_spectrum_text.text():
        spectrumType = r.spectraType.esdem
    else:
        QMessageBox(icon=QMessageBox.Icon.Critical, text='State cannot be identified for saving purposes').exec()
    amps_norm = np.divide(amps, np.linalg.norm(amps))
    ui.spectrumObject = r.esdSpectrum(spectrumType, list(x), list(yT), list(yFC), list(yHT), list(peaks), list(amps_norm))

def processESD(ui) -> None:
    try:
        del ui.spectrumObject
    except AttributeError:
        pass

    if ui.esd_total.isChecked():
        spectrumType = 'Total'
    elif ui.esd_fc.isChecked():
        spectrumType = 'Franck-Condon'
    elif ui.esd_ht.isChecked():
        spectrumType = 'Herzberg-Teller'

    processRange = (ui.esd_range_min.value(), ui.esd_range_max.value())
    smoothing = ui.esd_smoothing.value()
    offset = ui.esd_offset.value()

    x, yT, yFC, yHT = loadESD(ui)
    spectrumDict = {'Total': np.absolute(yT), 'Franck-Condon': np.absolute(yFC), 'Herzberg-Teller': np.absolute(yHT)}
    y = spectrumDict[spectrumType]

    ui.esd_ax1.plot(x, y)
    ui.esd_ax1.set_xlabel('Energy (eV)')
    ui.esd_ax1.set_ylabel('Amplitude')

    ysmoothed = gaussian_filter1d(y, smoothing)
    yoffset = np.multiply(ysmoothed, 1+offset)
    yout = []
    xout = []
    for (xpoint, ypoint, yoffsetpoint) in zip(x, y, yoffset):
        if yoffsetpoint < ypoint:
            yout += [ypoint]
            xout += [xpoint]

    ui.esd_ax2.plot(x, y)
    ui.esd_ax2.scatter(x, ysmoothed, s=2, c='k')
    ui.esd_ax2.scatter(x, yoffset, s=2, c='grey')
    ui.esd_ax2.scatter(xout, yout, s=20, c='r')

    outStr = ''
    for xpoint in xout:
        outStr += f'Peak at {xpoint:.3f} eV\n'

    ui.esd_output.setPlainText(outStr)
    buildESDSpectrumObject(ui, x, y, yFC, yHT, xout, yout)
    ui.esd_canvas.draw()
