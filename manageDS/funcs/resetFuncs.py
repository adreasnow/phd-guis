import resources as r
import pandas as pd
import numpy as np
from .classes import Ui

fluorophores, solvents, methods = r.fluorophores_solvents_methods()
config = r.loadConfig()

def make_multindex(cols: list[str], iterables: list, levelLabels: list[str], dfName: str, initValue, astype: type) -> None:
    rows = 1
    for inner in iterables:
        rows = rows * len(inner)
    index = pd.MultiIndex.from_product(iterables, names=levelLabels)
    df = pd.DataFrame(np.full((rows, len(cols)), initValue), columns=cols, index=index)
    df.astype(astype)
    df.to_pickle(f'{config.local.dbLocationMac}/{dfName}')

def resetDF(ui: Ui) -> None:
    ui.general_output.clear()
    fluorophores, solvents, methods = r.fluorophores_solvents_methods()
    if ui.resetWindow.reset_spectra.isChecked():
        make_multindex([i for i in r.Solvents if i.ds],
                       [[i for i in r.Fluorophores if i.experimental],
                           list(r.spectraType)],
                       ['Fluorophore', 'Spectrum'],
                       'spectra',
                       None, object)
        with r.statusLoad('spectra') as df:
            ui.general_output.setHtml(ui.general_output.toHtml() + '<h2>Spectra</h2>')
            dfOut = df.notnull().style.applymap(lambda x: 'color : blue' if x else 'color : red').to_html(max_rows=100)
            ui.general_output.setHtml(ui.general_output.toHtml() + dfOut)

    if ui.resetWindow.reset_energy.isChecked():
        make_multindex(solvents,
                       [[i for i in r.Fluorophores if i.gas or i.experimental],
                        ['a', 'a_g', 'e', 'e_g', 'zz', 'zz_g', 'qy', 'fl1-t', 'fl1-c', 'fl2-t', 'fl2-c']],
                       ['Fluorophore', 'Energy'],
                       'dataset',
                       0.0, object)
        with r.statusLoad('dataset') as df:
            ui.general_output.setHtml(ui.general_output.toHtml() + '<h2>Energy</h2>')
            dfOut = df.style.applymap(lambda x: 'color : blue' if x != None else 'color : red').format(precision=3).to_html(max_rows=100)
            ui.general_output.setHtml(ui.general_output.toHtml() + dfOut)

    if ui.resetWindow.reset_progress.isChecked():
        make_multindex(solvents,
                       [[i for i in r.Fluorophores if i.gas or i.revised],
                        [r.States.s0, r.States.s1, r.States.s2],
                        [i for i in r.MetaJobs if i.used]],
                       ['Fluorophore', 'State', 'MetaJob'],
                       'progress',
                       None, object)
        with r.statusLoad('progress') as df:
            ui.general_output.setHtml(ui.general_output.toHtml() + '<h2>Progress</h2>')
            dfOut = df.notnull().style.applymap(lambda x: 'color : blue' if x else 'color : red').to_html(max_rows=100)
            ui.general_output.setHtml(ui.general_output.toHtml() + dfOut)

    if ui.resetWindow.reset_freq.isChecked():
        make_multindex(solvents,
                       [[i for i in r.Fluorophores if i.gas or i.revised],
                        [r.States.s0, r.States.s1, r.States.s2],
                        [i for i in r.MetaJobs if i.job in [r.Jobs.freq, r.Jobs.casscfFreq] and i.used],
                        [i for i in r.Energy.Freq]],
                       ['Fluorophore', 'State', 'MetaJob', 'Property'],
                       'comp-freq',
                       None, object)
        with r.statusLoad('comp-freq') as df:
            ui.general_output.setHtml(ui.general_output.toHtml() + '<h2>Frequencies</h2>')
            dfOut = df.style.applymap(lambda x: 'color : blue' if x != None else 'color : red').format(precision=3).to_html(max_rows=100)
            ui.general_output.setHtml(ui.general_output.toHtml() + dfOut)

    if ui.resetWindow.reset_em.isChecked():
        make_multindex(solvents,
                       [[i for i in r.Fluorophores if i.gas or i.revised],
                        [r.States.s1, r.States.s2],
                        [i for i in r.MetaJobs if i.job == r.Jobs.em and i.used],
                        [i for i in r.Energy.Emission]],
                       ['Fluorophore', 'State', 'MetaJob', 'Property'],
                       'comp-em',
                       None, object)
        with r.statusLoad('comp-em') as df:
            ui.general_output.setHtml(ui.general_output.toHtml() + '<h2>Emission</h2>')
            dfOut = df.style.applymap(lambda x: 'color : blue' if x != None else 'color : red').format(precision=3).to_html(max_rows=100)
            ui.general_output.setHtml(ui.general_output.toHtml() + dfOut)

    if ui.resetWindow.reset_ex.isChecked():
        make_multindex(solvents,
                       [[i for i in r.Fluorophores if i.gas or i.revised],
                        [r.States.s0, r.States.s1, r.States.s2],
                        [i for i in r.MetaJobs if i.job == r.Jobs.ex and i.used],
                        [i for i in r.Energy.Excitation]],
                       ['Fluorophore', 'State', 'MetaJob', 'Property'],
                       'comp-ex',
                       None, object)
        with r.statusLoad('comp-ex') as df:
            ui.general_output.setHtml(ui.general_output.toHtml() + '<h2>Excitation</h2>')
            dfOut = df.style.applymap(lambda x: 'color : blue' if x != None else 'color : red').format(precision=3).to_html(max_rows=100)
            ui.general_output.setHtml(ui.general_output.toHtml() + dfOut)

    if ui.resetWindow.reset_cas.isChecked():
        make_multindex(solvents,
                       [[i for i in r.Fluorophores if i.gas or i.revised],
                        [r.States.s0, r.States.s1, r.States.s2],
                        [i for i in r.MetaJobs if i.job in [r.Jobs.nevpt2, r.Jobs.casscf] and i.used],
                        [i for i in r.Energy.CASSCF]],
                       ['Fluorophore', 'State', 'MetaJob', 'Property'],
                       'comp-casscf',
                       None, object)
        with r.statusLoad('comp-casscf') as df:
            ui.general_output.setHtml(ui.general_output.toHtml() + '<h2>CAS</h2>')
            dfOut = df.style.applymap(lambda x: 'color : blue' if x != None else 'color : red').format(precision=3).to_html(max_rows=100)
            ui.general_output.setHtml(ui.general_output.toHtml() + dfOut)

    if ui.resetWindow.reset_pol.isChecked():
        make_multindex([r.Solvents.gas],
                       [[i for i in r.Fluorophores if i.gas or i.revised],
                        [r.States.s0, r.States.s1, r.States.s2],
                        [i for i in r.MetaJobs if i.job in [r.Jobs.pol] and i.used],
                        [i for i in r.Energy.Polarisability]],
                       ['Fluorophore', 'State', 'MetaJob', 'Property'],
                       'comp-pol',
                       None, object)
        with r.statusLoad('comp-pol') as df:
            ui.general_output.setHtml(ui.general_output.toHtml() + '<h2>Polarisabilities</h2>')
            dfOut = df.style.applymap(lambda x: 'color : blue' if x != None else 'color : red').format(precision=3).to_html(max_rows=100)
            ui.general_output.setHtml(ui.general_output.toHtml() + dfOut)
