from .generalFuncs import extractIndices
from .visualisers import prettyDisplay
import resources as r
from .classes import Ui

def add_metajob(ui: Ui) -> None:
    metajob = ui.ar_metajob_metajob.currentData()

    for db in ['progress', 'comp-freq', 'comp-em', 'comp-ex', 'comp-casscf', 'comp-pol']:
        with r.statusLoad(df=db) as df:
            if db == 'progress':
                solvents, fluorophores, states, metajobs = extractIndices(df)
                for fluorophores in fluorophores:
                    for state in states:
                        df.loc[(fluorophores, state, metajob), :] = None
                        df.sort_index(inplace=True)
            else:
                solvents, fluorophores, states, metajobs, properties = extractIndices(df)
                if metajob.job == metajobs[0].job:
                    for solvent in solvents:
                        for fluorophore in fluorophores:
                            for state in states:
                                for prop in properties:
                                    df.loc[(fluorophore, state, metajob, prop), solvent] = 0.0
                                    df.sort_index(inplace=True)
    if ui.ar_show.isChecked():
        prettyDisplay(ui, full=True, uiOutput=ui.ar_output)

def rem_metajob(ui: Ui) -> None:
    metajob = ui.ar_metajob_metajob.currentData()
    for ds in ['progress', 'comp-freq', 'comp-em', 'comp-ex', 'comp-casscf', 'comp-pol']:
        with r.statusLoad(df=ds) as df:
            try:
                df = df.drop(index=metajob, level=2, inplace=True)
            except AttributeError:
                pass
            except KeyError:
                pass
    if ui.ar_show.isChecked():
        prettyDisplay(ui, full=True, uiOutput=ui.ar_output)

def add_fluorophore(ui: Ui) -> None:
    dbList = []
    if ui.ar_energy.isChecked():
        dbList += ['dataset']
    if ui.ar_progress.isChecked():
        dbList += ['progress']
    if ui.ar_spectra.isChecked():
        dbList += ['spectra']
    if ui.ar_freq.isChecked():
        dbList += ['comp-freq']
    if ui.ar_em.isChecked():
        dbList += ['comp-em']
    if ui.ar_ex.isChecked():
        dbList += ['comp-ex']
    if ui.ar_cas.isChecked():
        dbList += ['comp-casscf']
    if ui.ar_pol.isChecked():
        dbList += ['comp-pol']

    fluorophore = ui.ar_fluorophore_fluorophore.currentData()
    for db in dbList:
        initval = 0.0 if db in ['dataset'] else None
        with r.statusLoad(df=db) as df:
            if db == 'progress':
                solvents, fluorophores, states, metajobs = extractIndices(df)
                for state in states:
                    for metajob in metajobs:
                        df.loc[(fluorophore, state, metajob), :] = initval
                        df.sort_index(inplace=True)
            elif db in ['comp-freq', 'comp-em', 'comp-ex', 'comp-casscf', 'comp-pol']:
                solvents, fluorophores, states, metajobs, properties = extractIndices(df)
                for state in states:
                    for metajob in metajobs:
                        for prop in properties:
                            df.loc[(fluorophore, state, metajob, prop), :] = initval
                            df.sort_index(inplace=True)
            else:
                solvents, fluorophores, inners = extractIndices(df)
                for inner in inners:
                    df.loc[(fluorophore, inner), :] = initval
                    df.sort_index(inplace=True)
    if ui.ar_show.isChecked():
        prettyDisplay(ui, full=True, uiOutput=ui.ar_output)

def rem_fluorophore(ui: Ui) -> None:
    dbList = []
    if ui.ar_energy.isChecked():
        dbList += ['dataset']
    if ui.ar_progress.isChecked():
        dbList += ['progress']
    if ui.ar_spectra.isChecked():
        dbList += ['spectra']
    if ui.ar_freq.isChecked():
        dbList += ['comp-freq']
    if ui.ar_em.isChecked():
        dbList += ['comp-em']
    if ui.ar_ex.isChecked():
        dbList += ['comp-ex']
    if ui.ar_cas.isChecked():
        dbList += ['comp-casscf']
    if ui.ar_pol.isChecked():
        dbList += ['comp-pol']

    fluorophore = ui.ar_fluorophore_fluorophore.currentData()
    for db in dbList:
        with r.statusLoad(df=db) as df:
            try:
                df = df.drop(index=fluorophore, level=0, inplace=True)
            except AttributeError:
                pass
    if ui.ar_show.isChecked():
        prettyDisplay(ui, full=True, uiOutput=ui.ar_output)

def add_solvent(ui: Ui) -> None:
    dbList = []
    if ui.ar_energy.isChecked():
        dbList += ['dataset']
    if ui.ar_progress.isChecked():
        dbList += ['progress']
    if ui.ar_spectra.isChecked():
        dbList += ['spectra']
    if ui.ar_frerq.isChecked():
        dbList += ['comp-freq']
    if ui.ar_em.isChecked():
        dbList += ['comp-em']
    if ui.ar_ex.isChecked():
        dbList += ['comp-ex']
    if ui.ar_cas.isChecked():
        dbList += ['comp-casscf']
    if ui.ar_pol.isChecked():
        dbList += ['comp-pol']

    solvent = ui.ar_solvent_solvent.currentData()
    for db in dbList:
        initval = 0.0 if db in ['dataset'] else None
        with r.statusLoad(df=db) as df:
            if db == 'progress':
                solvents, fluorophores, states, metajobs = extractIndices(df)
                for fluorophore in fluorophores:
                    for state in states:
                        for metajob in metajobs:
                            df.loc[(fluorophore, state, metajob), solvent] = initval
                            df.sort_index(inplace=True)
            elif db in ['comp-freq', 'comp-em', 'comp-ex', 'comp-casscf']:
                solvents, fluorophores, states, metajobs, properties = extractIndices(df)
                for fluorophore in fluorophores:
                    for state in states:
                        for metajob in metajobs:
                            for prop in properties:
                                df.loc[(fluorophore, state, metajob, prop), solvent] = initval
                                df.sort_index(inplace=True)
            else:
                solvents, fluorophores, inners = extractIndices(df)
                for fluorophore in fluorophores:
                    for inner in inners:
                        df.loc[(fluorophore, inner), solvent] = initval
                        df.sort_index(inplace=True)
    if ui.ar_show.isChecked():
        prettyDisplay(ui, full=True, uiOutput=ui.ar_output)

def rem_solvent(ui: Ui) -> None:
    dbList = []
    if ui.ar_energy.isChecked():
        dbList += ['dataset']
    if ui.ar_progress.isChecked():
        dbList += ['progress']
    if ui.ar_spectra.isChecked():
        dbList += ['spectra']
    if ui.ar_frerq.isChecked():
        dbList += ['comp-freq']
    if ui.ar_em.isChecked():
        dbList += ['comp-em']
    if ui.ar_ex.isChecked():
        dbList += ['comp-ex']
    if ui.ar_cas.isChecked():
        dbList += ['comp-casscf']
    if ui.ar_pol.isChecked():
        dbList += ['comp-pol']

    solvent = ui.ar_solvent_solvent.currentData()
    for db in dbList:
        with r.statusLoad(df=db) as df:
            try:
                df = df.drop(solvent, axis=1, inplace=True)
            except AttributeError:
                pass
    if ui.ar_show.isChecked():
        prettyDisplay(ui, full=True, uiOutput=ui.ar_output)
