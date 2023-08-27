import numpy as np
import resources as r
from PyQt6.QtWidgets import QMessageBox
from .guiFuncs import add_items_list_dict, add_items_combo, add_items_combo_dict, add_items_list
from .classes import Ui
from .rateLimited import statusLoad_rl

def clear_lifetime_plot(ui: Ui):
    ui.ax_lifetime.cla()
    ui.ax_lifetime.autoscale_view()
    ui.ax_lifetime.relim()
    if "legend_lifetime" in ui.__dict__:
        ui.legend_lifetime.remove()

def expFunc(t: list[float], I0: int, τ: float) -> float:
    return np.multiply(np.exp(np.negative(np.divide(t, τ))), I0)

def expFuncWC(t: list[float], I0: int, τ: float, c: float) -> float:
    return np.multiply(expFunc(t, I0, τ), c)

def expFuncx2(t: list[float], I0: int, τ_1: float, c_1: float, τ_2: float, c_2: float) -> float:
    return np.add(np.multiply(expFunc(t, I0, τ_1), c_1),
                  np.multiply(expFunc(t, I0, τ_2), c_2))

def expFuncx3(t: list[float], I0: int, τ_1: float, c_1: float, τ_2: float, c_2: float, τ_3: float, c_3: float) -> float:
    return np.add(np.add(np.multiply(expFunc(t, I0, τ_1), c_1),
                         np.multiply(expFunc(t, I0, τ_2), c_2)),
                  np.multiply(expFunc(t, I0, τ_3), c_3))

def expFuncx4(t: list[float], I0: int, τ_1: float, c_1: float, τ_2: float, c_2: float, τ_3: float, c_3: float, τ_4: float, c_4: float) -> float:
    return np.add(np.add(np.add(np.multiply(expFunc(t, I0, τ_1), c_1),
                                np.multiply(expFunc(t, I0, τ_2), c_2)),
                         np.multiply(expFunc(t, I0, τ_3), c_3)),
                  np.multiply(expFunc(t, I0, τ_4), c_4))

def loadFLSpectrum(ui: Ui) -> None:
    xRange = (ui.fl_min_x_out.value(), ui.fl_max_x_out.value())
    plotData = ui.plotData.isChecked()
    printData = ui.printData.isChecked()
    verbose = ui.verbosePrint.isChecked()
    scale = ui.scale.isChecked()
    logPlot = ui.logPlot.isChecked()

    clear_lifetime_plot(ui)
    ui.output_lifetime.setPlainText('')

    FLFuncList = [expFuncWC, expFuncWC, expFuncx2, expFuncx3, expFuncx4]
    ui.ax_lifetime.axhline(0, c='k', lw=0.5)
    ui.ax_lifetime.axvline(0, c='k', lw=0.5)
    ui.ax_lifetime.set_xlabel('Time (ns)')
    ui.ax_lifetime.set_ylabel('Counts')
    ui.ax_lifetime.set_xlim(xRange[0], xRange[1])
    with statusLoad_rl('spectra') as df:
        for fluorophore in [i.data(1) for i in ui.fluorophoreList_widg.selectedItems()]:
            for solvent in [i.data(1) for i in ui.solventList_widg.selectedItems()]:
                try:
                    spectrum = df.at[(fluorophore, r.spectraType.lifetime), solvent]
                except KeyError:
                    spectrum = None
                if spectrum != None:
                    expCount = spectrum.expCount
                    popts = [spectrum.I0]
                    if printData:
                        ui.output_lifetime.setPlainText(ui.output_lifetime.toPlainText() + f'{fluorophore} in {solvent}:\n')
                        if verbose:
                            ui.output_lifetime.setPlainText(ui.output_lifetime.toPlainText() + f'Residual: {spectrum.residual:.8f}\n')
                            ui.output_lifetime.setPlainText(ui.output_lifetime.toPlainText() + f'𝜒²: {spectrum.chi2:.3f}\n')
                            ui.output_lifetime.setPlainText(ui.output_lifetime.toPlainText() + f'I0: {spectrum.I0:.0f}\n')

                    trfList = []
                    for count, trf_fit in enumerate(spectrum.trf_fitted):
                        trfList += [(trf_fit.c, trf_fit.t)]
                        popts += [trf_fit.t, trf_fit.c]
                    trfList = list(reversed(sorted(trfList)))
                    for i in trfList:
                        c, t = i
                        if printData:
                            ui.output_lifetime.setPlainText(ui.output_lifetime.toPlainText() + f'τ: {t:.2f}ns - {c:.1%}\n')
                    if printData:
                        ui.output_lifetime.setPlainText(ui.output_lifetime.toPlainText() + '\n')

                    y = spectrum.trf_convolved
                    x = [i*spectrum.binWidth*1e-3 for i in range(len(y))]
                    x = np.subtract(x, spectrum.offset*spectrum.binWidth*1e-3)
                    y_fit = FLFuncList[expCount](x, *popts)
                    if scale:
                        popts[0] = spectrum.I0
                        y_fit = FLFuncList[expCount](x, *popts)
                        y_flip = np.absolute(np.subtract(y_fit, 10000))

                        offset = x[list(y_flip).index(min(y_flip))]
                        x = np.subtract(x, offset)

                    if plotData:
                        ui.ax_lifetime.plot(x, y, label=f'{fluorophore}: {solvent} {r.spectraType.lifetime}')
                        ui.ax_lifetime.plot(x, y_fit, 'k--', lw=0.5)
                    else:
                        ui.ax_lifetime.plot(x, y_fit, label=f'{fluorophore}: {solvent} {r.spectraType.lifetime}')
    if logPlot:
        ui.ax_lifetime.set_yscale('log')
        ui.ax_lifetime.set_ylim(0.3, 12000)

    else:
        ui.ax_lifetime.set_ylim(-100, 12000)
    ui.legend_lifetime = ui.ax_lifetime.legend()
    ui.canvas_lifetime.draw()

def loadFromDSFL(ui: Ui) -> None:
    fluorophore = ui.saveLifetimeWindow.fluorophore.currentData()
    solvent = ui.saveLifetimeWindow.solvent.currentData()

    with r.statusLoad('spectra') as df:
        fl = df.at[(fluorophore, r.spectraType.lifetime), solvent]
    trfList = []
    try:
        for i in fl.trf_fitted:
            trfList += [(i.c, i.t)]
        flDict = {}
        trfList = list(reversed(sorted(trfList)))
        for i in trfList:
            c, t = i
            flDict[f'{c:.2%} - {t:.2f}ns'] = (t, c)
        add_items_list_dict(ui.saveLifetimeWindow.lifetimes, flDict)
    except AttributeError:
        QMessageBox(icon=QMessageBox.Icon.Critical, text=f'No Spectra imported for {fluorophore} in {solvent}').exec()

def saveToDSFL(ui: Ui) -> None:
    fluorophore = ui.saveLifetimeWindow.fluorophore.currentData()
    solvent = ui.saveLifetimeWindow.solvent.currentData()
    t1 = c1 = t2 = c2 = 0.00
    for count, i in enumerate([i.data(1) for i in ui.saveLifetimeWindow.lifetimes.selectedItems()]):
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

    QMessageBox(icon=QMessageBox.Icon.Information, text=f'Saved {fluorophore} in {solvent}!').exec()
