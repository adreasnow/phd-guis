import matplotlib.pyplot as plt
from pathlib import Path
import resources as r
import numpy as np
from functools import partial
from scipy.optimize import curve_fit
from phdimporter import TRF
from PyQt6.QtWidgets import QMessageBox, QFileDialog, QVBoxLayout, QLineEdit
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from .guiFuncs import add_items_combo, add_items_list_dict
from .generalFuncs import extractIndices
from .flExps import expFunc, expFuncWC
from .flExps import FLFuncList, FLLinFuncList
from .ui import Ui

def populate_fl(ui: Ui) -> None:
    with r.statusLoad('spectra') as df:
        solvents, fluorophores, spectra = extractIndices(df)
    add_items_combo(ui.fl_save_fluorophore, fluorophores)
    add_items_combo(ui.fl_save_solvent, solvents)
    loss = ['linear', 'soft_l1', 'huber', 'cauchy', 'arctan']
    add_items_combo(ui.fl_loss, loss)
    init_fl_plot(ui)

def connect_fl(ui: Ui) -> None:
    ui.fl_trf_button.clicked.connect(partial(trf_browse, ui))
    ui.fl_irf_button.clicked.connect(partial(irf_browse, ui))
    ui.fl_fit_button.clicked.connect(partial(plotFL, ui))
    ui.fl_save_button.clicked.connect(partial(saveToDSFL, ui))
    ui.fl_reset.clicked.connect(partial(fl_reset, ui))

def init_fl_plot(ui: Ui) -> None:
    ui.fl_layout = QVBoxLayout(ui.fl_frame)
    ui.fl_layout.setObjectName("fl_layout")
    ui.fl_figure, (ui.fl_ax1, ui.fl_ax3, ui.fl_ax2, ui.fl_ax4) = plt.subplots(4, 1, figsize=(8, 10), sharex=True, height_ratios=[3, 3, 1, 1])
    ui.fl_canvas = FigureCanvas(ui.fl_figure)
    ui.fl_toolbar = NavigationToolbar(ui.fl_canvas, ui)
    ui.fl_layout.addWidget(ui.fl_toolbar)
    ui.fl_layout.addWidget(ui.fl_canvas)

def clear_fl_plot(ui: Ui) -> None:
    for axes in [ui.fl_ax1, ui.fl_ax3, ui.fl_ax2, ui.fl_ax4]:
        axes.cla()
        axes.autoscale_view()
        axes.relim()


def trf_browse(ui: Ui) -> None:
    file_dialog = QFileDialog()
    directory = '/Users/adrea/gdrive/Monash/PhD/Fluorophore/data/tr'
    if ui.fl_trf_text.text() != '':
        path = Path(ui.fl_trf_text.text())
        if path.exists:
            directory = path.parent.as_posix()

    ui.fl_trf_text.setText(file_dialog.getOpenFileName(directory=directory, filter="PicoHarp binary or text file (*.phd *.txt)")[0])

def irf_browse(ui: Ui) -> None:
    file_dialog = QFileDialog()
    directory = '/Users/adrea/gdrive/Monash/PhD/Fluorophore/data/tr'
    if ui.fl_trf_text.text() != '':
        path = Path(ui.fl_trf_text.text())
        if path.exists:
            directory = path.parent.as_posix()
    ui.fl_irf_text.setText(file_dialog.getOpenFileName(directory=directory, filter="PicoHarp binary or text file (*.phd *.txt)")[0])

def fl_reset(ui: Ui) -> None:
    ui.fl_trf_text.setText('')
    ui.fl_irf_text.setText('')
    ui.fl_binSize_widg.setValue(0.0)
    ui.fl_startOffset_widg.setValue(0)
    ui.fl_maxTime_widg.setValue(1000)
    ui.fl_expCount_widg.setValue(1)
    ui.fl_max_x_out.setValue(20)
    ui.fl_max_x.setValue(20)
    ui.fl_scaled_widg.setChecked(True)
    ui.fl_logFit_widg.setChecked(False)
    ui.fl_plotIRF_widg.setChecked(False)
    ui.fl_output.setPlainText('')
    ui.fl_lifetimes.clear()
    ui.fl_save_fluorophore.setCurrentIndex(0)
    ui.fl_save_solvent.setCurrentIndex(0)

def saveToDSFL(ui: Ui) -> None:
    fluorophore = ui.fl_save_fluorophore.currentData()
    solvent = ui.fl_save_solvent.currentData()
    t1 = c1 = t2 = c2 = 0.00
    fl = [i.data(1) for i in ui.fl_lifetimes.selectedItems()]
    if len(fl) == 0:
        QMessageBox(icon=QMessageBox.Icon.Critical, text='Lifetime not fitted, or no litefimes selected').exec()
        return
    for count, i in enumerate(fl):
        if count == 0:
            t1, c1 = i
        elif count == 1:
            t2, c2 = i
        else:
            break

    cScale = 1/(c1+c2)
    c1 = c1*cScale
    c2 = c2*cScale

    with r.statusLoad('dataset') as df:
        df.at[(fluorophore, 'fl1-t'), solvent] = t1
        df.at[(fluorophore, 'fl1-c'), solvent] = c1
        df.at[(fluorophore, 'fl2-t'), solvent] = t2
        df.at[(fluorophore, 'fl2-c'), solvent] = c2

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

    QMessageBox(icon=QMessageBox.Icon.Information, text=f'Saved {fluorophore} in {solvent}!').exec()

def loadAndCull(ui: Ui, fc: QLineEdit) -> tuple[list[float], list[float], bool]:
    error = False
    x = []
    y = []
    if fc.text() == '':
        error = True
        QMessageBox(icon=QMessageBox.Icon.Critical, text='Files not Loaded').exec()
    else:
        nameList = fc.text().split('/')[-1].split('.')[0].split('_')
        for name in nameList:
            for fluorophore in r.Fluorophores:
                if name.lower() == fluorophore.name:
                    index = ui.fl_save_fluorophore.findData(fluorophore)
                    ui.fl_save_fluorophore.setCurrentIndex(index)
                    break
            for solvent in r.Solvents:
                if name.lower() == solvent.name:
                    index = ui.fl_save_solvent.findData(solvent)
                    ui.fl_save_solvent.setCurrentIndex(index)
                    break

        trf = TRF(fc.text())
        y = trf.y
        x = trf.x
        ui.fl_binSize_widg.setValue(trf.Resolution_int)
    return x, y, error

def chiSQ(y_obs: list[float], y_pred: list[float], popt: list[float]) -> float:
    dof = len(y_obs) - (len(popt))
    # ensure no divide by 0
    y_pred_max_1 = [i + 1 if i == 0 else i for i in y_pred]
    return np.sum(np.divide(np.square(np.subtract(y_obs, y_pred)), y_pred_max_1)) / len(y_pred)

def fitFL(ui: Ui, plot: bool = True, x_in: list[float] = None, y_in: list[float] = None,
          irf_in: list[float] = None) -> tuple[float, float, list[float], list[float]]:
    binSize = ui.fl_binSize_widg.value()
    expCount = ui.fl_expCount_widg.value()
    maxTime = ui.fl_maxTime_widg.value()
    startOffset = ui.fl_startOffset_widg.value()
    scale = ui.fl_scaled_widg.isChecked()
    irfPlot = ui.fl_plotIRF_widg.isChecked()
    logFit = ui.fl_logFit_widg.isChecked()

    outPrint = ''

    irf = irf_in
    irf = np.array(irf)

    irfMaxBin = irf.tolist().index(max(irf))
    for c, i in enumerate(irf[irfMaxBin:]):
        if i == 0:
            zeroBin = c + irfMaxBin
            break
    irf = irf[:zeroBin]

    for c, i in enumerate(reversed(irf[:irfMaxBin])):
        if i == 0:
            zeroBin = irfMaxBin - c
            break
    irf = irf[zeroBin:]

    x_raw = x_in
    y_raw = y_in

    max_y = max(y_raw)
    irf = list(reversed(irf))  # the kernel is flipped in convolutions
    y_raw = np.append(y_raw, np.zeros((len(y_raw), 1)))
    y_raw = np.convolve(y_raw, irf, 'full')
    x_raw = [i*binSize*1e-3 for i in range(len(y_raw))]

    y_raw = np.divide(y_raw, max(y_raw)/max_y)

    maxBins = int(maxTime*binSize*1e3)
    maxBin = y_raw.tolist().index(max(y_raw))
    for c, i in enumerate(y_raw[maxBin:]):
        if i == 0:
            zeroBin = c + maxBin
            break
    x_raw = x_raw[:zeroBin]
    y_raw = y_raw[:zeroBin]

    x_start = y_raw.tolist().index(max(y_raw)) + startOffset

    x_raw = np.subtract(x_raw, (x_start * binSize) / 1000)
    x = x_raw[x_start:]
    y = y_raw[x_start:]

    index = np.argmin(np.abs(np.array(x)-maxTime))
    cutoff = x[index]
    x = x[:index]
    y = y[:index]

    if plot:
        if irfPlot:
            ui.fl_ax3.plot([i*binSize*1e-3 for i in range(len(irf))], irf, c='g')
        x_func = np.arange(-5, ui.fl_max_x.value(), 0.01)
        fig, (ax1, ax3, ax2, ax4) = plt.subplots(4, 1, figsize=(8, 10), sharex=True, height_ratios=[3, 3, 1, 1])
        # Log Plot
        ui.fl_ax1.set_xlim(-5, ui.fl_max_x.value())
        ui.fl_ax1.set_yscale('log')
        ui.fl_ax1.set_ylim(1e-1, 1e5, auto=False)
        ui.fl_ax1.axhline(0, c='k', lw=0.5)
        ui.fl_ax1.axvline(0, c='k', lw=0.5)
        ui.fl_ax1.set_xlabel('Time (ns)')
        ui.fl_ax1.set_ylabel('Counts')
        ui.fl_ax1.axvline(cutoff, c='r', lw=0.5)
        ui.fl_ax1.scatter(x_raw, y_raw, s=0.1)

        # Linear plot
        ui.fl_ax3.set_ylim(-300, max(y_raw)+300, auto=False)
        ui.fl_ax3.set_ylabel('Counts')
        ui.fl_ax3.axvline(0, c='k', lw=0.5)
        ui.fl_ax3.axvline(cutoff, c='r', lw=0.5)
        ui.fl_ax3.scatter(x_raw, y_raw, s=0.1)

        # Residuals
        # ui.fl_ax2.set_xlabel('Time (ns)')
        ui.fl_ax2.set_ylabel('Residuals\n(exp)')
        ui.fl_ax2.axvline(0, c='k', lw=0.5)
        ui.fl_ax2.axhline(0, c='k', lw=0.5)

        # Residuals
        ui.fl_ax4.set_xlabel('Time (ns)')
        ui.fl_ax4.set_ylabel('Residuals\n(lin)')
        ui.fl_ax4.axvline(0, c='k', lw=0.5)
        ui.fl_ax4.axhline(0, c='k', lw=0.5)

    popt, residual = fitLifetime(ui, x, y)
    I0 = popt[0]
    popt_culled = popt[1:]
    trf_fit = []

    cList = []
    for i in range(expCount):
        cList += [popt_culled[(i * 2) + 1]]
    cList_norm = np.multiply(cList, 1 / np.sum(cList))

    I0 = I0 / (1 / np.sum(cList))

    popt = [I0]
    τList = []
    for i in range(expCount):
        τ = popt_culled[i * 2]
        τList += [τ]
        c = cList_norm[i]
        popt += [τ, c]

    chi2 = chiSQ(FLFuncList[expCount](x, *popt), y, popt)
    chi2_log = chiSQ(FLLinFuncList[expCount](x, *popt), np.log(y), popt)

    if plot:
        outPrint += f'𝜒² (lin space): {chi2:.4f}\n'
        outPrint += f'Residual: {residual:.8f}\n'
        outPrint += f'I0: {I0:.2f}\n'
        for i in range(expCount):
            τ = popt_culled[i * 2]
            c = cList_norm[i]
            outPrint += f'τ: {τ:.2f}\n'
            outPrint += f'Contribution: {c*100:.2f}%\n'
            trf_fit += [r.trf(τ, c)]
            if scale:
                ui.fl_ax1.plot(x_func, expFuncWC(x_func, I0, τ, c), 'g--', lw=0.5)
                ui.fl_ax3.plot(x_func, expFuncWC(x_func, I0, τ, c), 'g--', lw=0.5)
            else:
                ui.fl_ax1.plot(x_func, expFunc(x_func, I0, τ), 'g--', lw=0.5)
                ui.fl_ax3.plot(x_func, expFunc(x_func, I0, τ), 'g--', lw=0.5)
        ui.fl_ax1.plot(x_func, FLFuncList[expCount](x_func, *popt), 'k--', lw=1)
        ui.fl_ax3.plot(x_func, FLFuncList[expCount](x_func, *popt), 'k--', lw=1)
        # ui.fl_ax1.scatter([d], [I0], c='purple')
        residualList = np.subtract(FLLinFuncList[expCount](x, *popt), np.log(y))
        ui.fl_ax2.scatter(x, residualList, s=0.1)
        residualList = np.subtract(FLFuncList[expCount](x, *popt), y)
        ui.fl_ax4.scatter(x, residualList, s=0.1)
        ui.fl_canvas.draw()
        ui.fl_output.setPlainText(outPrint)

        ui.spectrumObject = r.Lifetime(r.spectraType.lifetime,
                                       irf, y_in, y_raw,
                                       trf_fit, binSize,
                                       residual, chi2, I0,
                                       x_start)
        SetupDsFl(ui)

    return residual, chi2, popt, τList

def fitLifetime(ui: Ui, x: list[float], y: list[float]) -> tuple[list[float], float]:
    expCount = ui.fl_expCount_widg.value()
    loss = ui.fl_loss.currentData()

    minbounds = [max(y) - 500]
    maxbounds = [max(y) + 500]

    fitFunc = FLFuncList[expCount]
    if ui.fl_logFit_widg.isChecked():
        y = np.log(y)
        fitFunc = FLLinFuncList[expCount]

    for i in range(expCount):
        minbounds += [0, 0]
        maxbounds += [99999999, 1]

    popt, pcov = curve_fit(fitFunc, x, y,
                           bounds=(minbounds, maxbounds),
                           loss=loss,
                           max_nfev=999999999999,
                           # verbose=2,
                           )

    residual = np.sum(np.subtract(y, FLFuncList[expCount](x, *popt)))

    return popt, residual

def plotFL(ui: Ui) -> None:
    try:
        del ui.spectrumObject
    except AttributeError:
        pass

    if "fl_ax1" in ui.__dict__:
        clear_fl_plot(ui)
    _, irf, error = loadAndCull(ui, ui.fl_irf_text)
    if error:
        return
    x, y, error = loadAndCull(ui, ui.fl_trf_text)
    if error:
        return
    fitFL(ui, x_in=x, y_in=y, irf_in=irf)

def SetupDsFl(ui: Ui) -> None:
    trfList = []
    for i in ui.spectrumObject.trf_fitted:
        trfList += [(i.c, i.t)]
    flDict = {}
    trfList = list(reversed(sorted(trfList)))
    for i in trfList:
        c, t = i
        flDict[f'{c:.2%} {t:.2f}ns'] = (t, c)
    add_items_list_dict(ui.fl_lifetimes, flDict)
