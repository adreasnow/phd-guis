import resources as r
import numpy as np
import matplotlib.pyplot as plt
from functools import partial
from pathlib import Path
from resources.specCorr import PMCorrect
from PyQt6.QtWidgets import QMessageBox, QFileDialog, QVBoxLayout
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from .guiFuncs import add_items_combo, setup_QRangeSlider
from .generalFuncs import extractIndices
from .ui import Ui

def populate_spectra(ui: Ui) -> None:
    init_spectra_plot(ui)
    with r.statusLoad('spectra') as df:
        solvents, fluorophores, _ = extractIndices(df)
    add_items_combo(ui.spectra_fluorophore, fluorophores)
    add_items_combo(ui.spectra_solvent, solvents)
    setup_QRangeSlider(ui.spectra_clip_range, 200, 850, output=(ui.spectra_clip_min, ui.spectra_clip_max))

def connect_spectra(ui: Ui) -> None:
    ui.ex_file_button.clicked.connect(partial(ex_file_browse, ui))
    ui.ex_solv_button.clicked.connect(partial(ex_solv_browse, ui))
    ui.fluo_file_button.clicked.connect(partial(fluo_file_browse, ui))
    ui.fluo_solv_button.clicked.connect(partial(fluo_solv_browse, ui))
    ui.abs_file_button.clicked.connect(partial(abs_file_browse, ui))
    ui.spectra_load.clicked.connect(partial(loadSpectra, ui))
    ui.spectra_save.clicked.connect(partial(saveSpectra, ui))
    ui.spectra_reset.clicked.connect(partial(spectra_reset, ui))


def init_spectra_plot(ui: Ui) -> None:
    ui.spectra_layout = QVBoxLayout(ui.spectra_frame)
    ui.spectra_layout.setObjectName("spectra_layout")
    ui.spectra_figure, (ui.spectra_ax1) = plt.subplots(1, 1, figsize=(8, 6))
    ui.spectra_canvas = FigureCanvas(ui.spectra_figure)
    ui.spectra_toolbar = NavigationToolbar(ui.spectra_canvas, ui)
    ui.spectra_layout.addWidget(ui.spectra_toolbar)
    ui.spectra_layout.addWidget(ui.spectra_canvas)


def spectra_reset(ui: Ui) -> None:
    ui.ex_file_text.setText('')
    ui.ex_solv_text.setText('')
    ui.fluo_file_text.setText('')
    ui.fluo_solv_text.setText('')
    ui.abs_file_text.setText('')
    ui.spectra_clip_min.setValue(200)
    ui.spectra_clip_max.setValue(850)
    ui.spectra_autoclip.setChecked(False)
    ui.spectra_scaleSolv.setValue(1.0)
    ui.spectra_baseline_none.setChecked(True)
    ui.spectra_baseline_shift.setChecked(False)
    ui.spectra_baseline_level.setChecked(False)
    ui.spectra_output.setPlainText('')
    ui.spectra_fluorophore.setCurrentIndex(0)
    ui.spectra_solvent.setCurrentIndex(0)

def ex_file_browse(ui: Ui) -> None:
    file_dialog = QFileDialog()
    directory = '/Users/adrea/gdrive/Monash/PhD/Fluorophore/data/ex/'
    if ui.ex_file_text.text() != '':
        path = Path(ui.ex_file_text.text())
        if path.exists:
            directory = path.parent.as_posix()
    ui.ex_file_text.setText(file_dialog.getOpenFileName(directory=directory, filter="Comma Separated Value Files (*.csv)")[0])

def ex_solv_browse(ui: Ui) -> None:
    file_dialog = QFileDialog()
    directory = '/Users/adrea/gdrive/Monash/PhD/Fluorophore/data/ex/'
    if ui.ex_file_text.text() != '':
        path = Path(ui.ex_file_text.text())
        if path.exists:
            directory = path.parent.as_posix()
    ui.ex_solv_text.setText(file_dialog.getOpenFileName(directory=directory, filter="Comma Separated Value Files (*.csv)")[0])

def fluo_file_browse(ui: Ui) -> None:
    file_dialog = QFileDialog()
    directory = '/Users/adrea/gdrive/Monash/PhD/Fluorophore/data/fluor/'
    if ui.fluo_file_text.text() != '':
        path = Path(ui.fluo_file_text.text())
        if path.exists:
            directory = path.parent.as_posix()
    ui.fluo_file_text.setText(file_dialog.getOpenFileName(directory=directory, filter="Comma Separated Value Files (*.csv)")[0])

def fluo_solv_browse(ui: Ui) -> None:
    file_dialog = QFileDialog()
    directory = '/Users/adrea/gdrive/Monash/PhD/Fluorophore/data/fluor/'
    if ui.fluo_file_text.text() != '':
        path = Path(ui.fluo_file_text.text())
        if path.exists:
            directory = path.parent.as_posix()
    ui.fluo_solv_text.setText(file_dialog.getOpenFileName(directory=directory, filter="Comma Separated Value Files (*.csv)")[0])

def abs_file_browse(ui: Ui) -> None:
    file_dialog = QFileDialog()
    directory = '/Users/adrea/gdrive/Monash/PhD/Fluorophore/data/abs/'
    if ui.abs_file_text.text() != '':
        path = Path(ui.abs_file_text.text())
        if path.exists:
            directory = path.parent.as_posix()
    ui.abs_file_text.setText(file_dialog.getOpenFileName(directory=directory, filter="Comma Separated Value Files (*.csv)")[0])


def clear_fl_plot(ui: Ui) -> None:
    ui.spectra_ax1.cla()
    ui.spectra_ax1.autoscale_view()
    ui.spectra_ax1.relim()

def saveSpectra(ui: Ui) -> None:
    fluorophore = ui.spectra_fluorophore.currentData()
    solvent = ui.spectra_solvent.currentData()
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


def baseLineCorrect(y: np.array, shift: bool, level: bool) -> np.array:
    if shift:
        y = np.subtract(y, min(y))
        shiftAmount = [min(y) for i in range(len(y))]
    if level:
        y = np.subtract(y, min(y))
        maxLoc = list(y).index(max(y))
        lower = y[0:maxLoc]
        lowerLoc = list(lower).index(min(lower))
        upper = y[maxLoc:-1]
        upperLoc = list(upper).index(min(upper))

        innerRange = (upperLoc + len(lower)) - lowerLoc
        interval = ((min(lower) - min(upper)) / innerRange)
        shiftAmount = [i * interval for i in range(1, len(y) + 1)]
        shiftAmount = np.subtract(shiftAmount, (len(y) - upperLoc) * interval)
        y = np.add(y, shiftAmount)
        y = np.subtract(y, min(y))
    return y

def clipFunc(x: list[float], y: list[float], units: str = 'eV', x_solv: list[float] = [],
             y_solv: list[float] = []) -> tuple[list[float], list[float]] | tuple[list[float], list[float], list[float], list[float]]:
    maxLoc = list(y).index(max(y))
    lower = y[0:maxLoc]
    lowerLoc = list(lower).index(min(lower))
    upper = y[maxLoc:-1]
    upperLoc = list(upper).index(min(upper))

    less = np.less(x, x[upperLoc + len(lower)])
    more = np.greater(x, x[lowerLoc])
    xor = np.logical_xor(less, more)
    x = np.delete(x, xor)
    y = np.delete(y, xor)
    if x_solv != [] and y_solv != []:
        x_solv = np.delete(x_solv, xor)
        y_solv = np.delete(y_solv, xor)
        return x, y, x_solv, y_solv
    else:
        return x, y

def loadCSV(file: str, clip: tuple[float, float], spectraType: r.spectraType, scale: int = 1.0) -> tuple[list[float], list[float], r.spectraType]:
    if file == None:
        QMessageBox(icon=QMessageBox.Icon.Critical, text='Files not Loaded').exec()
        return [], [], 0, False
    x, y = ([], [])
    enLambda = 0
    printedNM = False
    with open(file, 'r') as f:
        lines = f.readlines()
    for line in lines:
        CSV = True if ',' in line else False
        if CSV:
            splitline = line.split(',')
        else:
            splitline = line.split()

        if (('Ex. Wavelength (nm)' in line) or ('Em. Wavelength (nm)' in line)) and not printedNM:
            enLambda = int(round(float(line.split()[-1]), 0))
            printedNM = True

        try:
            if len(splitline) != 1:
                x_temp, y_temp = [float(i) for i in splitline[0:2]]
                x += [int(round(x_temp, 0))]
                y += [y_temp]

        except ValueError:
            pass
        except IndexError:
            pass

    x_ev = r.nmToEv(x)
    if clip[1] > max(x_ev) or clip[0] < min(x_ev):
        QMessageBox(icon=QMessageBox.Icon.Critical, text='Clip is out of bounds').exec()
        return [], [], 0, False

    less = np.less(x_ev, clip[1])
    more = np.greater(x_ev, clip[0])
    xor = np.logical_xor(less, more)
    x = np.delete(x, xor)
    y = np.delete(y, xor)
    if spectraType in [r.spectraType.emission, r.spectraType.excitation]:
        y = PMCorrect(x, y, spectraType, enLambda)
    y = np.multiply(y, scale)
    return x, y, enLambda, True

def processBasicSpectra(spectrum_file: str, clip: tuple[int, int], autoClip: bool, baseLine: str, spectraType: r.spectraType, scaleSolv: float, solv_file: str = None) -> r._simpleSpectrum | tuple[r._simpleSpectrum, r._simpleSpectrum]:
    clip = (r.nmToEv(clip[0]), r.nmToEv(clip[1]))
    x, y, _, check = loadCSV(spectrum_file, clip, spectraType)
    if not check:
        if solv_file == None:
            return 'fail'
        else:
            return 'fail', False
    if solv_file != None:
        x_solv, y_solv, _, check = loadCSV(solv_file, clip, spectraType, scaleSolv)
        if not check:
            if solv_file == None:
                return 'fail'
            else:
                return 'fail', False

        for i in range(200, 900):
            if i in x and i in x_solv:
                spectrum_start_index = list(x).index(i)
                solvent_start_index = list(x_solv).index(i)
                break
        for i in reversed(range(200, 900)):
            if i in x and i in x_solv:
                spectrum_end_index = list(x).index(i)
                solvent_end_index = list(x_solv).index(i)
                break

        for spectrum_i, solvent_i in zip(list(range(spectrum_start_index, spectrum_end_index)), list(range(solvent_start_index, solvent_end_index))):
            y[spectrum_i] = y[spectrum_i] - y_solv[solvent_i]

    if baseLine != 'None':
        baseLineShift = True if baseLine == 'Shift' else False
        baseLineLevel = True if baseLine == 'Level' else False
        y = baseLineCorrect(y, baseLineShift, baseLineLevel)
        if solv_file != None:
            y_solv = baseLineCorrect(y_solv, baseLineShift, baseLineLevel)

    if autoClip:
        if solv_file != None:
            x, y, x_solv, y_solv = clipFunc(x, y, units='nm', x_solv=x_solv, y_solv=y_solv)
        else:
            x, y = clipFunc(x, y, units='nm')

    if solv_file != None:
        return r._simpleSpectrum(x=x, y=y, ), r._simpleSpectrum(x=x_solv, y=y_solv)
    else:
        return r._simpleSpectrum(x=x, y=y)


def loadSpectra(ui: Ui) -> None:
    try:
        del ui.spectrumObject
    except AttributeError:
        pass

    clear_fl_plot(ui)
    ui.spectra_ax1.set_ylabel("Response (AU)")
    ui.spectra_ax1.set_xlabel("λ (nm)")
    ui.spectra_ax1.axhline(0, c='k', lw=0.5)
    clip = (ui.spectra_clip_min.value(), ui.spectra_clip_max.value())
    autoClip = ui.spectra_autoclip.isChecked()
    if ui.spectra_baseline_none.isChecked():
        baseLine = 'None'
    elif ui.spectra_baseline_shift.isChecked():
        baseLine = 'Shift'
    elif ui.spectra_baseline_level.isChecked():
        baseLine = 'Level'
    scaleSolv = ui.spectra_scaleSolv.value()

    spectrumDict = {0: r.spectraType.excitation, 1: r.spectraType.emission, 2: r.spectraType.absorbance}
    widgDict = {0: ui.ex_file_text.text(), 1: ui.fluo_file_text.text(), 2: ui.abs_file_text.text()}
    solvWidgDict = {0: ui.ex_solv_text.text(), 1: ui.fluo_solv_text.text(), 2: None}
    spectraType = spectrumDict[ui.spectra_tabs.currentIndex()]
    spectrum_file = widgDict[ui.spectra_tabs.currentIndex()]
    solv_file = solvWidgDict[ui.spectra_tabs.currentIndex()]

    if (spectrum_file == '') or (solv_file == ''):
        QMessageBox(icon=QMessageBox.Icon.Critical, text='Files not Loaded').exec()
    else:
        nameList = spectrum_file.split('/')[-1].split('.')[0].split('_')
        for name in nameList:
            for fluorophore in r.Fluorophores:
                if name.lower() == fluorophore.name:
                    index = ui.spectra_fluorophore.findData(fluorophore)
                    ui.spectra_fluorophore.setCurrentIndex(index)
                    break
            for solvent in r.Solvents:
                if name.lower() == solvent.name:
                    index = ui.spectra_solvent.findData(solvent)
                    ui.spectra_solvent.setCurrentIndex(index)
                    break

        if solv_file == None:
            spectrum = processBasicSpectra(spectrum_file, clip, autoClip, baseLine, spectraType, scaleSolv)
            if spectrum == 'fail':
                return
            ui.spectra_ax1.plot(spectrum.x, spectrum.y)
            ui.spectrumObject = r.spectrum(spectraType, spectrum, deconvoluted=False)
        elif solv_file != None:
            spectrum, solvSpectrum = processBasicSpectra(spectrum_file, clip, autoClip, baseLine, spectraType, scaleSolv, solv_file=solv_file)
            if spectrum == 'fail':
                return
            ui.spectra_ax1.plot(spectrum.x, spectrum.y)
            ui.spectra_ax1.plot(solvSpectrum.x, solvSpectrum.y, 'r', linewidth=0.5)
            ui.spectrumObject = r.spectrum(spectraType, spectrum, deconvoluted=False, solventSpectrum=solvSpectrum)
        else:
            QMessageBox(icon=QMessageBox.Icon.Critical, text='Solvent response required').exec()
        ui.spectra_canvas.draw()
