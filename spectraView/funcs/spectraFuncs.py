import numpy as np
import resources as r
import matplotlib.pyplot as plt
from scipy.ndimage import gaussian_filter1d
from scipy.signal import savgol_filter
from PyQt6.QtWidgets import QMessageBox
from resources.deconv import gaussian0_func, gaussian1_func, gaussian2_func, gaussian3_func
from .classes import Ui
from .rateLimited import statusLoad_rl

def clear_spectra_plot(ui: Ui) -> None:
    ui.ax_spectra.cla()
    ui.ax_spectra.autoscale_view()
    ui.ax_spectra.relim()
    if "legend_spectra" in ui.__dict__:
        ui.legend_spectra.remove()

def loadSpectrum(ui: Ui) -> None:
    clear_spectra_plot(ui)
    ui.output_spectra.setPlainText('')

    deriv = 1 if ui.deriv.isChecked() else 0
    smoothing = ui.derivSmooth.isChecked()
    plotGaussians = ui.plotGauss.isChecked()
    printGaussians = ui.printGauss.isChecked()
    printESD = ui.printESD.isChecked()
    printlmax = ui.printLMax.isChecked()
    norm = ui.norm.currentText()
    units = ui.units.currentText()
    gaussAmps = (ui.amp_low.value(), ui.amp_high.value())
    esdOffset = ui.esd_offset.value()

    printed = False
    ui.ax_spectra.axhline(0, c='k', lw=0.5)
    with statusLoad_rl('spectra') as df:
        for fluorophore in [i.data(1) for i in ui.fluorophoreList_widg.selectedItems()]:
            for solvent in [i.data(1) for i in ui.solventList_widg.selectedItems()]:
                for spectraType in [i.data(1) for i in ui.spectraList_widg.selectedItems()]:

                    try:
                        spectrum = df.at[(fluorophore, spectraType), solvent]
                        if spectrum.spectraType in [r.spectraType.emission, r.spectraType.excitation, r.spectraType.absorbance]:
                            x = spectrum.spectrum.x
                            if units == 'eV':
                                x = r.nmToEv(x)
                            y = spectrum.spectrum.y
                            if deriv != 0:
                                for i in range(spectrum.derivLevel):
                                    y = np.gradient(y, x)
                                    if spectrum.smoothing_deriv > 0 and smoothing:
                                        y = gaussian_filter1d(y, spectrum.smoothing_deriv)

                            if norm == 'Normalise' or deriv == 1:
                                y = np.divide(y, np.linalg.norm(y))
                            elif norm == 'Equal λ max':
                                y = np.divide(y, np.max(y))
                            if printlmax:
                                maxVal = y.tolist().index(max(y))
                                lmax = x[maxVal]
                                if units == 'eV':
                                    lmax = f'{lmax:.3f}'
                                else:
                                    lmax = f'{lmax:.0f}'
                                ui.output_spectra.setPlainText(ui.output_spectra.toPlainText() + f'λmax = {lmax}\n')

                            ui.output_spectra.setPlainText(ui.output_spectra.toPlainText() + f'{fluorophore} in {solvent}:\n')
                            if not spectrum.deconvoluted:
                                ui.ax_spectra.plot(x, y, label=f'{fluorophore}: {solvent} {spectraType}')
                                if ui.savgol.isChecked():
                                    y_smoothed = savgol_filter(y, ui.savgol_level.value(), 2)
                                    ui.ax_spectra.plot(x, y_smoothed, 'k:', linewidth=1)
                            else:
                                if (spectrum.derivLevel > 0 and deriv == 1) or deriv == 0:
                                    ui.ax_spectra.plot(x, y, label=f'{fluorophore}: {solvent} {spectraType}')
                                    if ui.savgol.isChecked():
                                        y_smoothed = savgol_filter(y, ui.savgol_level.value(), 2)
                                        ui.ax_spectra.plot(x, y_smoothed, 'k:', linewidth=1)
                                    if plotGaussians:
                                        if deriv == 0:
                                            peaks = spectrum.peaks_sorted
                                        else:
                                            peaks = spectrum.peaks_sorted_deriv

                                        if printGaussians:
                                            ui.output_spectra.setPlainText(ui.output_spectra.toPlainText() + 'Gaussians:\n')
                                        for count, gauss in enumerate(peaks):
                                            amp = gauss.amplitude
                                            if norm == 'Equal λmax' and deriv == 0:
                                                amp = amp * (np.linalg.norm(spectrum.spectrum.y) / np.max(spectrum.spectrum.y))
                                            elif norm == 'None' and deriv == 0:
                                                amp = amp * np.linalg.norm(spectrum.spectrum.y)

                                            if units == 'nm' and not printed:
                                                printed = True
                                            elif units == 'eV':
                                                if amp >= gaussAmps[0] and amp <= gaussAmps[1]:
                                                    gaussianFuncDict = {1: gaussian1_func, 2: gaussian2_func, 3: gaussian3_func}
                                                    if deriv == 1:
                                                        gaussian_func = gaussianFuncDict[spectrum.derivLevel]
                                                    else:
                                                        gaussian_func = gaussian0_func

                                                    ui.ax_spectra.fill_between(x, gaussian_func(x, amp, gauss.center, gauss.width), alpha=0.3)
                                                if printGaussians and amp >= gaussAmps[0] and amp <= gaussAmps[1]:
                                                    ui.output_spectra.setPlainText(ui.output_spectra.toPlainText() + f'{gauss.center:.3f} eV ({r.evToNm(gauss.center):.0f} nm), μ: {amp:.3f}, σ: {gauss.width:.3f}\n')
                                else:
                                    ui.output_spectra.setPlainText(ui.output_spectra.toPlainText() + f'{spectraType} spectrum of {fluorophore} in {solvent} was not performed in deriv space.')


                        if spectraType in [r.spectraType.esdem, r.spectraType.esdex]:
                            label = f'{fluorophore}: {solvent} ESD {"emission" if spectraType == r.spectraType.esdem else "excitation"}'
                            if spectraType == r.spectraType.esdem:
                                peaks = list(reversed(spectrum.peaks))
                            else:
                                peaks = spectrum.peaks
                            if units == 'nm':
                                peaks = r.evToNm(peaks)

                            markerline, stemlines, baseline = ui.ax_spectra.stem(np.add(peaks, esdOffset), spectrum.amps, linefmt='-', label=label)
                            plt.setp(markerline, linewidth=0, markersize=2)
                            plt.setp(stemlines, linewidth=0.3)
                            plt.setp(stemlines, 'color', plt.getp(markerline, 'color'))
                            plt.setp(baseline, linewidth=0, markersize=0)
                            if printESD:
                                print(f'\nESD {"emission" if spectraType == r.spectraType.esdem else "excitation"}')

                                for xpoint in peaks:
                                    print(f'Peak at {xpoint + esdOffset:.3f} eV')
                    except KeyError:
                        pass
                    except AttributeError:
                        pass

    if len(ui.ax_spectra.lines) > 1:
        ui.ax_spectra.set_ylabel("Absorbance/Emission")
        ui.ax_spectra.set_xlabel(f"λ ({units})")
        if units == 'eV':
            if ui.ax_spectra.xaxis_inverted:
                ui.ax_spectra.invert_xaxis()
        elif units == 'nm':
            if not ui.ax_spectra.xaxis_inverted:
                ui.ax_spectra.invert_xaxis()
        ui.legend_spectra = ui.figure_spectra.legend()
        ui.canvas_spectra.draw()

def loadFromDS(ui: Ui) -> None:
    fluorophore = ui.saveSpectrumWindow.fluorophore.currentData()
    solvent = ui.saveSpectrumWindow.solvent.currentData()
    with r.statusLoad('dataset') as df:
        ui.saveSpectrumWindow.a.setValue(df.at[(fluorophore, 'a'), solvent])
        ui.saveSpectrumWindow.e.setValue(df.at[(fluorophore, 'e'), solvent])
        ui.saveSpectrumWindow.a_g.setValue(df.at[(fluorophore, 'a_g'), solvent])
        ui.saveSpectrumWindow.e_g.setValue(df.at[(fluorophore, 'e_g'), solvent])
        ui.saveSpectrumWindow.zz.setValue(df.at[(fluorophore, 'zz'), solvent])
        ui.saveSpectrumWindow.zz_g.setValue(df.at[(fluorophore, 'zz_g'), solvent])

def saveToDS(ui: Ui) -> None:
    fluorophore = ui.saveSpectrumWindow.fluorophore.currentData()
    solvent = ui.saveSpectrumWindow.solvent.currentData()

    with r.statusLoad('dataset') as df:
        if ui.saveSpectrumWindow.a.value() != 0.0:
            df.at[(fluorophore, 'a'), solvent] = ui.saveSpectrumWindow.a.value()
        if ui.saveSpectrumWindow.e.value() != 0.0:
            df.at[(fluorophore, 'e'), solvent] = ui.saveSpectrumWindow.e.value()
        if ui.saveSpectrumWindow.a_g.value() != 0.0:
            df.at[(fluorophore, 'a_g'), solvent] = ui.saveSpectrumWindow.a_g.value()
        if ui.saveSpectrumWindow.e_g.value() != 0.0:
            df.at[(fluorophore, 'e_g'), solvent] = ui.saveSpectrumWindow.e_g.value()
        if ui.saveSpectrumWindow.zz.value() != 0.0:
            df.at[(fluorophore, 'zz'), solvent] = ui.saveSpectrumWindow.zz.value()
        if ui.saveSpectrumWindow.zz_g.value() != 0.0:
            df.at[(fluorophore, 'zz_g'), solvent] = ui.saveSpectrumWindow.zz_g.value()
        QMessageBox(icon=QMessageBox.Icon.Information, text=f'Saved {fluorophore} in {solvent}!').exec()

def saveToDS_reset(ui: Ui) -> None:
    fluorophore = ui.saveSpectrumWindow.fluorophore.currentData()
    solvent = ui.saveSpectrumWindow.solvent.currentData()

    with r.statusLoad('dataset') as df:
        df.at[(fluorophore, 'a'), solvent] = 0.00
        df.at[(fluorophore, 'e'), solvent] = 0.00
        df.at[(fluorophore, 'a_g'), solvent] = 0.00
        df.at[(fluorophore, 'e_g'), solvent] = 0.00
        df.at[(fluorophore, 'zz'), solvent] = 0.00
        df.at[(fluorophore, 'zz_g'), solvent] = 0.00
        ui.saveSpectrumWindow.a.setValue(0.00)
        ui.saveSpectrumWindow.e.setValue(0.00)
        ui.saveSpectrumWindow.a_g.setValue(0.00)
        ui.saveSpectrumWindow.e_g.setValue(0.00)
        ui.saveSpectrumWindow.zz.setValue(0.00)
        ui.saveSpectrumWindow.zz_g.setValue(0.00)
        QMessageBox(icon=QMessageBox.Icon.Information, text=f'{fluorophore} in {solvent} has been reset!').exec()
