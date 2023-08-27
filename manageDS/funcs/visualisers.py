import resources as r
import pandas as pd
import numpy as np
import pathlib
from seaborn import light_palette
from rdkit import Chem
from rdkit.Chem import Draw
from PIL.ImageQt import ImageQt
from PyQt6 import uic
from PyQt6.QtGui import QPixmap, QFont
from PyQt6.QtWidgets import QDialog, QTextEdit, QLabel
from copy import deepcopy
from .generalFuncs import extractIndices
from .classes import Ui

class visDS(QDialog):
    def __init__(self):
        super().__init__()
        uic.loadUi(f'{pathlib.Path(__file__).parent.resolve()}/../visDS.ui', self)

def visualise_ds(ui: Ui) -> None:

    ui.visDS = visDS()


    label = QLabel()
    label.setText('Dataset')
    label.setFont(QFont('Arial', 20))
    ui.visDS.verticalLayout_2.addWidget(label)
    mols = []
    nameList = []
    for fluorophore in r.Fluorophores:
        if fluorophore.revised:
            nameList += [fluorophore.fluorophore]
            mols += [Chem.MolFromSmiles(fluorophore.smiles)]
    pm1 = QPixmap.fromImage(ImageQt(Draw.MolsToGridImage(mols, legends=nameList, subImgSize=(400, 400))))
    label = QLabel()
    label.setPixmap(pm1)
    ui.visDS.verticalLayout_2.addWidget(label)


    label = QLabel()
    label.setText('Gas Phase')
    label.setFont(QFont('Arial', 20))
    ui.visDS.verticalLayout_2.addWidget(label)
    mols = []
    nameList = []
    for fluorophore in r.Fluorophores:
        if fluorophore.gas:
            nameList += [fluorophore.fluorophore]
            mols += [Chem.MolFromSmiles(fluorophore.smiles)]
    pm2 = QPixmap.fromImage(ImageQt(Draw.MolsToGridImage(mols, legends=nameList, subImgSize=(400, 400))))
    label = QLabel()
    label.setPixmap(pm2)
    ui.visDS.verticalLayout_2.addWidget(label)

    ui.visDS.show()


def showDF(ui: Ui) -> None:
    prettyDisplay(ui)

def prettyDisplay(ui: Ui, full: bool = False, uiOutput: QTextEdit = None) -> None:
    output = ui.general_output if uiOutput == None else uiOutput
    output.clear()
    stateList = []
    if ui.general_s0.isChecked():
        stateList += [r.States.s0]
    if ui.general_s1.isChecked():
        stateList += [r.States.s1]
    if ui.general_s2.isChecked():
        stateList += [r.States.s2]

    if ui.general_progress.isChecked() and not full:
        with r.statusLoad('progress') as df:
            metajobList = [i.data(1) for i in ui.general_metajobs.selectedItems()]
            if full:
                _, _, _, metajobList = extractIndices(df)
            for metajob in metajobList:
                output.setHtml(output.toHtml() + f'<h2>{metajob}</h2>')
                states = deepcopy(stateList)
                if not metajob.gs:
                    try:
                        states.remove(r.States.s0)
                    except ValueError:
                        pass
                if not metajob.es:
                    try:
                        states.remove(r.States.s1)
                    except ValueError:
                        pass
                    try:
                        states.remove(r.States.s2)
                    except ValueError:
                        pass

                for state in states:
                    output.setHtml(output.toHtml() + f'<h3>{state}</h3>')
                    dfOut = df.loc[(slice(None), state, metajob)].style\
                                                                 .applymap(lambda x: 'color : red' if x == r.Status.failed else '')\
                                                                 .applymap(lambda x: 'color : teal' if x == r.Status.finished else '')\
                                                                 .applymap(lambda x: 'color : orange' if x == r.Status.running else '')\
                                                                 .applymap(lambda x: 'color : blue' if x == r.Status.queued else '')\
                                                                 .applymap(lambda x: 'color : purple' if x == r.Status.timed_out else '')\
                                                                 .applymap(lambda x: 'color : grey' if x == None else '').to_html()
                    output.setHtml(output.toHtml() + dfOut)

    if ui.general_spectra.isChecked() or full:
        with r.statusLoad('spectra') as df:
            dfOut = df.notnull().style.applymap(lambda x: 'color : blue' if x else 'color : red').to_html()
            output.setHtml(output.toHtml() + dfOut)

    if ui.general_energy.isChecked() or full:
        with r.statusLoad('dataset') as df:
            dfOut = df.style.applymap(lambda x: 'color : blue' if x not in [None, 0.00] else 'color : red').format(precision=3).to_html()
            output.setHtml(output.toHtml() + dfOut)

    if ui.general_freq.isChecked() or full:
        with r.statusLoad('comp-freq') as df:
            dfOut = df.style.applymap(lambda x: 'color : blue' if x != None else 'color : red').format(precision=3).to_html(max_rows=100)
            output.setHtml(output.toHtml() + dfOut)

    if ui.general_excitation.isChecked() or full:
        with r.statusLoad('comp-ex') as df:
            dfOut = df.style.applymap(lambda x: 'color : blue' if x != None else 'color : red').format(precision=3).to_html(max_rows=100)
            output.setHtml(output.toHtml() + dfOut)

    if ui.general_emission.isChecked() or full:
        with r.statusLoad('comp-em') as df:
            dfOut = df.style.applymap(lambda x: 'color : blue' if x != None else 'color : red').format(precision=3).to_html(max_rows=100)
            output.setHtml(output.toHtml() + dfOut)

    if ui.general_cas.isChecked() or full:
        with r.statusLoad('comp-casscf') as df:
            dfOut = df.style.applymap(lambda x: 'color : blue' if x != None else 'color : red').format(precision=3).to_html(max_rows=100)
            output.setHtml(output.toHtml() + dfOut)
            print('done')

    if ui.general_pol.isChecked() or full:
        with r.statusLoad('comp-pol') as df:
            dfOut = df.style.applymap(lambda x: 'color : blue' if x != None else 'color : red').format(precision=3).to_html(max_rows=100)
            output.setHtml(output.toHtml() + dfOut)


def timedOut(ui: Ui) -> None:
    ui.general_output.clear()
    clusters = []
    if ui.general_m3.isChecked():
        clusters += [r.clusters.m3]
    if ui.general_monarch.isChecked():
        clusters += [r.clusters.monarch]
    if ui.general_gadi.isChecked():
        clusters += [r.clusters.gadi]

    for cluster in clusters:
        ui.general_output.setPlainText(ui.general_output.toPlainText() + f'{cluster}:\n')
        with r.clusterHandler(cluster) as clu:
            jobs = clu.timed_out()
        for job in jobs:
            ui.general_output.setPlainText(ui.general_output.toPlainText() + job + '\n')
        ui.general_output.setPlainText(ui.general_output.toPlainText() + '\n')

def viewSolvents(ui: Ui) -> None:
    fluorophores, solvents, methods = r.fluorophores_solvents_methods()
    headers = ['ε', 'n', 'η', 'ρ', 'α', 'β', 'γ', 'φ', 'ψ', 'χ (fast)', 'χ (slow)']
    solventDict = {}
    for solvent in solvents:
        solventDict[solvent.solvent] = [round(solvent.e, 2),
                                        solvent.n,
                                        solvent.eta,
                                        solvent.rho,
                                        solvent.a,
                                        solvent.b,
                                        solvent.g,
                                        solvent.p,
                                        solvent.s,
                                        ((solvent.n**2) - 1) / (solvent.e - 1),
                                        (solvent.e - (solvent.n**2)) / (solvent.e - 1)]

    cmap = light_palette('#a275ac', as_cmap=True)
    df = pd.DataFrame.from_dict(solventDict, orient='index', columns=headers)
    dfOut = df.style.background_gradient(cmap=cmap).format(precision=2).to_html()
    ui.general_output.setPlainText('')
    ui.general_output.setHtml(dfOut)


def printDBSelection(ui: Ui, dfName: str) -> None:
    ui.select_output.clear()
    widgDict = {'comp-ex': [ui.select_ex_states, ui.select_ex_metajobs, ui.select_ex_properties],
                'comp-em': [ui.select_em_states, ui.select_em_metajobs, ui.select_em_properties],
                'comp-freq': [ui.select_freq_states, ui.select_freq_metajobs, ui.select_freq_properties],
                'comp-casscf': [ui.select_cas_states, ui.select_cas_metajobs, ui.select_cas_properties],
                'comp-pol': [ui.select_pol_states, ui.select_pol_metajobs, ui.select_pol_properties],
                }
    cmap = light_palette('#a275ac', as_cmap=True)

    with r.statusLoad(df=dfName) as df:
        for prop in [i.data(1) for i in widgDict[dfName][2].selectedItems()]:
            precision = 0 if 'neg' in prop.name else 6 if 'de' in prop.name else 6 if 'zpve' in prop.name else 3
            astype = object if 't_' in prop.name else float
            astype2 = float if (('t_' in prop.name) and (ui.select_pol_vecs.isChecked())) else object if (('t_' in prop.name) and (not ui.select_pol_vecs.isChecked())) else float
            astype = object if dfName == 'comp-pol' and prop != r.Energy.Polarisability.iso else float
            if dfName == 'comp-pol':
                astype2 = astype
                filteredSolvents = [r.Solvents.gas]
            else:
                filteredSolvents = [i.data(1) for i in ui.select_solvents.selectedItems()]

            def isNaNFunc(x) -> bool:
                if type(x) not in [float, int]:
                    if x == None:
                        return True
                    else:
                        return False
                else:
                    if pd.isna(x):
                        return True
                    else:
                        return False

            dfOut = df.loc[([i.data(1) for i in ui.select_fluorophores.selectedItems()],
                           [i.data(1) for i in widgDict[dfName][0].selectedItems()],
                           [i.data(1) for i in widgDict[dfName][1].selectedItems()],
                           prop),
                           filteredSolvents]\
                      .astype(astype)\
                      .applymap(lambda x: np.linalg.norm(np.array(x)) if type(x) == tuple and ui.select_pol_vecs.isChecked() else x)\
                      .astype(astype2)\
                      .style.background_gradient(cmap=cmap, axis=1)\
                      .applymap(lambda x: 'color: red' if isNaNFunc(x) else '')\
                      .applymap(lambda x: 'background-color: transparent' if isNaNFunc(x) else '')\
                      .format(precision=precision).to_html()
            ui.select_output.setHtml(ui.select_output.toHtml() + dfOut)
