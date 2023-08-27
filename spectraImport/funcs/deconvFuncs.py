import resources as r
import matplotlib.pyplot as plt

import numpy as np
from functools import partial
from scipy.optimize import curve_fit
from scipy.ndimage import gaussian_filter1d
from scipy.signal import savgol_filter
from PyQt6.QtWidgets import QMessageBox, QVBoxLayout
from PyQt6.QtCore import QCoreApplication
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from resources.deconv import gaussian0FuncList, gaussian1FuncList, gaussian2FuncList, gaussian3FuncList
from resources.deconv import gaussian0FuncList as funcList
from resources.deconv import gaussian0_func, gaussian1_func, gaussian2_func, gaussian3_func
from resources.deconv.lorentzian0 import lorentzian0_func, lorentzian0FuncList
from resources.deconv.voigt0 import voigt0_func, voigt0FuncList

from .ui import Ui
from .guiFuncs import add_items_combo, setup_QRangeSlider
from .generalFuncs import extractIndices

def populate_deconv(ui: Ui) -> None:
    with r.statusLoad('spectra') as df:
        solvents, fluorophores, spectra = extractIndices(df)
    add_items_combo(ui.deconv_fluorophore, fluorophores)
    add_items_combo(ui.deconv_solvent, solvents)
    add_items_combo(ui.deconv_spectrum, [r.spectraType.emission, r.spectraType.excitation, r.spectraType.absorbance])
    setup_QRangeSlider(ui.deconv_fitting_range, 140, 619, output=(ui.deconv_fitting_min, ui.deconv_fitting_max), outscale=0.01)
    setup_QRangeSlider(ui.deconv_amps_range, 1, 6000, values=(1, 5000), output=(ui.deconv_amps_min, ui.deconv_amps_max), outscale=0.0001)
    setup_QRangeSlider(ui.deconv_widths_range, 1, 2000, values=(1, 700), output=(ui.deconv_widths_min, ui.deconv_widths_max), outscale=0.0001)
    setup_QRangeSlider(ui.deconv_gauss_range, 1, 20, values=(1, 15), output=(ui.deconv_gauss_min, ui.deconv_gauss_max))
    setup_QRangeSlider(ui.deconv_refitting_range, 0, 400, values=(0, 400), output=(ui.deconv_refitting_min, ui.deconv_refitting_max), outscale=0.01)
    init_deconv_plot(ui)

def connect_deconv(ui: Ui) -> None:
    ui.deconv_deconv.clicked.connect(partial(deconv, ui))
    ui.deconv_save.clicked.connect(partial(saveDeconv, ui))
    ui.deconv_reset.clicked.connect(partial(reset_deconv, ui))

def reset_deconv(ui: Ui) -> None:
    ui.deconv_fluorophore.setCurrentIndex(0)
    ui.deconv_solvent.setCurrentIndex(0)
    ui.deconv_spectrum.setCurrentIndex(0)
    ui.deconv_function.setCurrentIndex(0)
    ui.deconv_deriv.setValue(1)
    ui.deconv_fitting_min.setValue(1.4)
    ui.deconv_fitting_max.setValue(6.19)
    ui.deconv_amps_min.setValue(0.0001)
    ui.deconv_amps_max.setValue(0.1)
    ui.deconv_widths_min.setValue(0.0001)
    ui.deconv_widths_max.setValue(0.07)
    ui.deconv_conv.setValue(3)
    ui.deconv_gauss_min.setValue(1)
    ui.deconv_gauss_max.setValue(15)
    ui.deconv_smoothing_nonderiv.setValue(10)
    ui.deconv_smoothing_deriv.setValue(5)
    ui.deconv_smoothing_raw.setValue(0)
    ui.deconv_smoothing_algorithm.setCurrentIndex(0)
    ui.deconv_savgol_polyorder.setValue(2)
    ui.deconv_savgolderivlevel.setValue(1)
    ui.deconv_maxiter.setValue(5000)
    ui.deconv_refitting_min.setValue(0.0)
    ui.deconv_refitting_max.setValue(4.0)
    ui.deconv_output.clear()

def init_deconv_plot(ui: Ui) -> None:
    ui.deconv_layout = QVBoxLayout(ui.deconv_frame)
    ui.deconv_layout.setObjectName("deconv_layout")
    ui.deconv_figure, (ui.deconv_ax1, ui.deconv_ax2, ui.deconv_ax3, ui.deconv_ax4) = plt.subplots(4, 1, figsize=(8, 8), sharex=True, height_ratios=[3, 1, 3, 1])
    ui.deconv_canvas = FigureCanvas(ui.deconv_figure)
    ui.deconv_toolbar = NavigationToolbar(ui.deconv_canvas, ui)
    ui.deconv_layout.addWidget(ui.deconv_toolbar)
    ui.deconv_layout.addWidget(ui.deconv_canvas)

def clear_deconv_plot(ui: Ui) -> None:
    for axes in [ui.deconv_ax1, ui.deconv_ax3, ui.deconv_ax2, ui.deconv_ax4]:
        axes.cla()
        axes.autoscale_view()
        axes.relim()
    ui.deconv_ax4.invert_xaxis()

def setup_progress(ui: Ui, total: int) -> None:
    ui.deconv_progress.setValue(0)
    ui.deconv_progress.setMaximum(total)
    QCoreApplication.processEvents()

def update_progress(ui: Ui) -> None:
    ui.deconv_progress.setValue(ui.deconv_progress.value() + 1)
    QCoreApplication.processEvents()

def deconv(ui: Ui) -> None:
    try:
        del ui.spectrumObject
    except AttributeError:
        pass
    clear_deconv_plot(ui)
    ui.deconv_output.clear()
    ui.deconv_deconv.setEnabled(False)
    fit(ui)
    ui.deconv_deconv.setEnabled(True)
    ui.deconv_canvas.draw()

def saveDeconv(ui: Ui) -> None:
    fluorophore = ui.deconv_fluorophore.currentData()
    solvent = ui.deconv_solvent.currentData()
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

def process(x: list[float], y: list[float], ngauss: int, amp: tuple[float, float],
            sigma: tuple[float, float], maxIter: int, fittingRange: tuple[float, float], derivFuncList: list[object]) -> tuple[list[float], float, list[float], list[float], bool]:
    xnew = []
    ynew = []
    for (xpoint, ypoint) in zip(x, y):
        if xpoint > fittingRange[0] and xpoint < fittingRange[1]:
            xnew += [xpoint]
            ynew += [ypoint]

    x = xnew
    y = ynew

    minbounds = []
    maxbounds = []
    for i in range(ngauss):
        minbounds += [amp[0], min(x), sigma[0]]
        maxbounds += [amp[1], max(x), sigma[1]]

    try:
        popt_gauss, pcov_gauss = curve_fit(derivFuncList[ngauss], x, y, bounds=(minbounds, maxbounds), maxfev=maxIter)
        error = False
    except RuntimeError as e:
        QMessageBox(icon=QMessageBox.Icon.Information, text=f'{e}\n\nYour input spectra may need clipping').exec()
        return [0.0], 0.0, [0.0], [0.0], True

    amps = []
    for count, i in enumerate(popt_gauss):
        if count % 3 == 0:
            amps += [i]

    residual = np.abs(np.sum(np.subtract(y, derivFuncList[ngauss](x, *popt_gauss))))
    return amps, residual, popt_gauss, pcov_gauss, error

def backProcess(x: list[float], y: list[float], amp: tuple[float, float], sigma: tuple[float, float],
                locList: list[float], ampList: list[float], maxIter: int, ampCutoff: tuple[float, float], funcList: list[object]) -> tuple[list[float], float, list[float], list[float]]:

    culledLocList = []
    for i in zip(locList, ampList):
        # print(i[0], i[1])
        if i[1] <= 1 * (10**(- ampCutoff[0])) and i[1] >= 1 * (10**(- ampCutoff[1])):
            culledLocList += [i[0]]

    ngauss = len(culledLocList)
    minbounds = []
    maxbounds = []
    for i in culledLocList:
        minbounds += [amp[0], i - 0.001, sigma[0]]
        maxbounds += [amp[1], i + 0.001, sigma[1]]

    popt_gauss, pcov_gauss = curve_fit(funcList[ngauss], x, y, bounds=(minbounds, maxbounds), maxfev=maxIter)

    amps = []
    for count, i in enumerate(popt_gauss):
        if count % 3 == 0:
            amps += [i]

    residual = np.abs(np.sum(np.subtract(y, funcList[ngauss](x, *popt_gauss))))
    return amps, residual, popt_gauss, pcov_gauss, ngauss

def smoothing(algorithm: str, y: list[float], level: int, savgolPoly: int, savgolDeriv: int) -> list[float]:
    if algorithm == 'Gaussian':
        y = gaussian_filter1d(y, level)
    elif algorithm == 'Savitzky-Golay':
        y = savgol_filter(y, level, savgolPoly, deriv=savgolDeriv)
    return y

def buildSpectrumObject(spectrum: r.spectrum, amp, sigma, convergence, gaussRange, maxIter, derivLevel,
                        residual, gaussObjectList, smoothingPre, smoothingDeriv,
                        residual_deriv=None, peaks_deriv=None) -> r.spectrum:

    params = r.deconvParams(amp, sigma, convergence, gaussRange, maxIter)

    return r.spectrum(spectrum.spectraType,
                      spectrum.spectrum,
                      True,
                      derivLevel,
                      params,
                      residual,
                      gaussObjectList,
                      smoothingPre,
                      smoothingDeriv,
                      residual_deriv=residual_deriv,
                      peaks_deriv=peaks_deriv,
                      solventSpectrum=spectrum.solventSpectrum
                      )

def fit(ui: Ui) -> None:
    fluorophore = ui.deconv_fluorophore.currentData()
    solvent = ui.deconv_solvent.currentData()
    spectraType = ui.deconv_spectrum.currentData()
    function = ui.deconv_function.currentText()
    fittingRange = (ui.deconv_fitting_min.value(), ui.deconv_fitting_max.value())
    amp = (ui.deconv_amps_min.value(), ui.deconv_amps_max.value())
    sigma = (ui.deconv_widths_min.value(), ui.deconv_widths_max.value())
    convergence = ui.deconv_conv.value()
    gaussRange = (ui.deconv_gauss_min.value(), ui.deconv_gauss_max.value())
    smoothingPre = ui.deconv_smoothing_nonderiv.value()
    smoothingDeriv = ui.deconv_smoothing_deriv.value()
    smoothingRaw = ui.deconv_smoothing_raw.value()
    smoothingType = ui.deconv_smoothing_algorithm.currentText()
    savgolPoly = ui.deconv_savgol_polyorder.value()
    savgolDeriv = ui.deconv_savgolderivlevel.value()
    maxIter = ui.deconv_maxiter.value()
    ampCutoff = (ui.deconv_refitting_min.value(), ui.deconv_refitting_max.value())
    derivLevel = ui.deconv_deriv.value()

    if smoothingType == 'Savitzky-Golay':
        if (savgolPoly >= smoothingPre and smoothingPre > 0) or \
           (savgolPoly >= smoothingDeriv and smoothingDeriv > 0) or \
           (savgolPoly >= smoothingRaw and smoothingRaw > 0):
            QMessageBox(icon=QMessageBox.Icon.Critical, text='Savitzky-Golay poly order must be less than the window length').exec()
            return



    # import the spectrum
    with r.statusLoad('spectra') as df:
        try:
            spectrum = df.at[(fluorophore, spectraType), solvent]
            if spectrum != None:
                x_nm = spectrum.spectrum.x
                y = spectrum.spectrum.y
            else:
                QMessageBox(icon=QMessageBox.Icon.Information, text='Spectrum not imported').exec()
                return
        except KeyError:
            QMessageBox(icon=QMessageBox.Icon.Information, text='Fluorophore/Solvent combo not found').exec()
            return

    x = r.nmToEv(x_nm)

    # optional raw smoothing
    if smoothingRaw > 0:
        y = smoothing(smoothingType, y, smoothingRaw, savgolPoly, savgolDeriv)

    # normalise the spectrum
    y_norm = np.divide(y, np.linalg.norm(y))
    y_zeroth = y_norm

    # optional pre smoothing
    if smoothingPre > 0:
        y_norm = smoothing(smoothingType, y_norm, smoothingPre, savgolPoly, savgolDeriv)

    # set the derivative level and function
    if derivLevel == 0 and function == 'Gaussian':
        derivFuncList = gaussian0FuncList
        gaussian_func = gaussian0_func
    elif derivLevel == 1 and function == 'Gaussian':
        derivFuncList = gaussian1FuncList
        gaussian_func = gaussian1_func
    elif derivLevel == 2 and function == 'Gaussian':
        derivFuncList = gaussian2FuncList
        gaussian_func = gaussian2_func
    elif derivLevel == 3 and function == 'Gaussian':
        derivFuncList = gaussian3FuncList
        gaussian_func = gaussian3_func
    elif derivLevel == 0 and function == 'Lorentzian':
        derivFuncList = lorentzian0FuncList
        gaussian_func = lorentzian0_func
    elif derivLevel == 0 and function == 'Voigt':
        derivFuncList = voigt0FuncList
        gaussian_func = voigt0_func
    else:
        QMessageBox(icon=QMessageBox.Icon.Critical, text='Function/derivative level combination not supported').exec()
        return

    # differentiate and optionally smooth
    for i in range(derivLevel):
        y_norm = np.gradient(y_norm, x)
        if smoothingDeriv > 0:
            y_norm = smoothing(smoothingType, y_norm, smoothingDeriv, savgolPoly, savgolDeriv)
    # differentiation makes things small so normalise again
    y_norm = np.divide(y_norm, np.linalg.norm(y_norm))

    converged = False
    # fitting cycle
    setup_progress(ui, gaussRange[1]-gaussRange[0])
    for ngauss in range(gaussRange[0], gaussRange[1]):
        amps, residual, popt_gauss, pcov_gauss, error = process(x, y_norm, ngauss, amp, sigma, maxIter, fittingRange, derivFuncList)
        if error:
            converged = False
            break

        # conv = 1 * 10**(- convergence)
        conv = convergence
        if residual <= conv:
            opt_ngauss = ngauss
            converged = True
            break
        ui.statusBar().showMessage(f'Fitting {ngauss} Gaussians - Residual {residual:.4f}/{conv:.4f}')
        update_progress(ui)

    # plot the spectra if they don't converge
    if not converged:
        ui.statusBar().showMessage("Not Converged!")
        ui.deconv_ax1.plot(x, y_norm, 'red', lw=1)
        ui.deconv_ax1.axhline(0, c='k', lw=0.5)
        ui.deconv_ax1.set_ylabel("Absorbance/Emission (AU)")
        ui.deconv_ax3.plot(x, y_zeroth, 'red', lw=1)
        ui.deconv_ax3.axhline(0, c='k', lw=0.5)
        ui.deconv_ax3.set_ylabel("Absorbance/Emission (AU)")
        ui.deconv_ax4.set_xlabel("Energy (eV)")
        return
    else:
        ui.statusBar().showMessage("Converged!")
        ui.deconv_progress.setValue(ui.deconv_progress.maximum())

    gauss = []
    gaussObjectList = []
    count = 1
    for i in popt_gauss:
        if count != 3:
            gauss += [i]
            count += 1
        else:
            count = 1
            loc = round(gauss[1], 3)
            nm = int(round(r.evToNm(loc), 0))

            gaussObjectList += [r.gaussian(loc, i, gauss[0])]
            gauss = []

    # plot the fitted functions
    for i in range(0, ngauss * 3, 3):
        ui.deconv_ax1.fill_between(x, gaussian_func(x, *popt_gauss[i:i + 3]), alpha=0.3)
    ui.deconv_ax1.plot(x, y_norm, 'red', lw=1)
    ui.deconv_ax1.plot(x, derivFuncList[ngauss](x, *popt_gauss), 'k--', lw=1)
    ui.deconv_ax1.axhline(0, c='k', lw=0.5)
    if derivLevel == 0:
        ui.deconv_ax1.set_ylabel("Absorbance/Emission (AU)")
    else:
        ui.deconv_ax1.set_ylabel(f"Absorbance/Emission (AU)\nderiv ({derivLevel}) space")
    ui.deconv_ax2.set_xlabel("E (eV)")
    ui.deconv_ax2.set_ylabel('Residuals')
    ui.deconv_ax2.axhline(0, c='k', lw=0.5)
    residualList = np.subtract(derivFuncList[ngauss](x, *popt_gauss), y_norm)
    xresidnew = []
    yresidnew = []
    for (xpoint, ypoint) in zip(x, residualList):
        if xpoint > fittingRange[0] and xpoint < fittingRange[1]:
            xresidnew += [xpoint]
            yresidnew += [ypoint]
    ui.deconv_ax2.scatter(xresidnew, yresidnew, s=0.1)
    if derivLevel != 0:
        ui.deconv_ax2.set_xlabel('')
        ui.deconv_ax3.plot(x, y_zeroth, 'red', lw=1)
        locList = popt_gauss[1::3]
        ampList = popt_gauss[0::3]

        amps_nonDeriv, residual_nonDeriv, popt_gauss_nonDeriv, pcov_gauss_nonDeriv, culledNgauss = backProcess(x, y_zeroth, amp, sigma, locList, ampList, maxIter, ampCutoff, funcList)
        gauss_nonDeriv = []
        gaussObjectList_nonDeriv = []
        count = 1
        for i in popt_gauss_nonDeriv:
            if count != 3:
                gauss_nonDeriv += [i]
                count += 1
            else:
                count = 1
                loc = round(gauss_nonDeriv[1], 3)
                gaussObjectList_nonDeriv += [r.gaussian(loc, i, gauss_nonDeriv[0])]
                gauss_nonDeriv = []

        ui.deconv_ax3.plot(x, funcList[culledNgauss](x, *popt_gauss_nonDeriv), 'k--', lw=1)
        for i in range(0, culledNgauss * 3, 3):
            ui.deconv_ax3.fill_between(x, gaussian0_func(x, *popt_gauss_nonDeriv[i:i + 3]), alpha=0.3)
        ui.deconv_ax3.axhline(0, c='k', lw=0.5)
        ui.deconv_ax3.set_ylabel("Absorbance/Emission (AU)\nnon-deriv space")
        ui.deconv_ax4.set_xlabel("E (eV)")
        ui.deconv_ax4.set_ylabel('Residuals')
        ui.deconv_ax4.axhline(0, c='k', lw=0.5)
        residualList_nonDeriv = np.subtract(funcList[culledNgauss](x, *popt_gauss_nonDeriv), y_zeroth)
        xresidnew = []
        yresidnew = []
        for (xpoint, ypoint) in zip(x, residualList_nonDeriv):
            if xpoint > fittingRange[0] and xpoint < fittingRange[1]:
                xresidnew += [xpoint]
                yresidnew += [ypoint]
        ui.deconv_ax4.scatter(xresidnew, yresidnew, s=0.1)

    if derivLevel == 0:
        ui.spectrumObject = buildSpectrumObject(spectrum, amp, sigma, convergence, gaussRange, maxIter, derivLevel,
                                                residual, gaussObjectList, smoothingPre, smoothingDeriv)
    else:
        ui.spectrumObject = buildSpectrumObject(spectrum, amp, sigma, convergence, gaussRange, maxIter, derivLevel,
                                                residual_nonDeriv, gaussObjectList_nonDeriv, smoothingPre, smoothingDeriv,
                                                residual, gaussObjectList)

    outStr = ''
    if derivLevel != 0:
        outStr += '### Deriv Fit ####\n'
    outStr += f'Residual: {residual:.4f} ≤ {conv:.4f}\n'
    outStr += f'Gaussians: {ngauss}\n'
    if derivLevel != 0:
        for gauss in ui.spectrumObject.peaks_sorted_deriv:
            outStr += f'{gauss.center:.3f} eV ({r.evToNm(gauss.center):.0f} nm) \namp: {gauss.amplitude:.5f}  \nwidth: {gauss.width:.3f}\n\n'
    else:
        for gauss in ui.spectrumObject.peaks_sorted:
            outStr += f'{gauss.center:.3f} eV ({r.evToNm(gauss.center):.0f} nm) \namp: {gauss.amplitude:.5f}  \nwidth: {gauss.width:.3f}\n\n'

    if derivLevel != 0:
        outStr += '\n### Re-Fit ###\n'
        outStr += f'Residual: {residual_nonDeriv:.2e}\n'
        outStr += f'Gaussians: {culledNgauss}\n'
        for gauss in ui.spectrumObject.peaks_sorted:
            outStr += f'{gauss.center:.3f} eV ({r.evToNm(gauss.center):.0f} nm) \namp: {gauss.amplitude:.5f}  \nwidth: {gauss.width:.3f}\n\n'
    ui.deconv_output.setPlainText(outStr)
