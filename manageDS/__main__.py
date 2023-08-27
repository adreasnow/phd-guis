import sys
import resources as r
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import QThreadPool
from functools import partial
from .funcs.generalFuncs import extractIndices
from .funcs.guiFuncs import add_items_list, add_items_combo
from .funcs.visualisers import timedOut, viewSolvents, visualise_ds, prettyDisplay, printDBSelection
from .funcs.pullFuncs import Runner
from .funcs.dfManipulation import add_metajob, rem_metajob, add_fluorophore, rem_fluorophore, add_solvent, rem_solvent
from .funcs.resetFuncs import resetDF
from .funcs.classes import Ui, ResetWindow
import qtawesome as qta

def reset_window(ui: Ui) -> None:
    ui.resetWindow = ResetWindow()
    ui.resetWindow.reset_button.clicked.connect(partial(resetDF, ui))
    ui.resetWindow.show()

def populate(ui: Ui) -> None:
    config = r.loadConfig()
    fluorophores, solvents, methods = r.fluorophores_solvents_methods()
    with r.statusLoad('progress') as df:
        metajobs = extractIndices(df)[3]

    # general
    add_items_list(ui.general_metajobs, metajobs)

    # selective results
    add_items_list(ui.select_fluorophores, [i for i in r.Fluorophores if (i.revised or i.gas)])
    add_items_list(ui.select_solvents, solvents)

    # add/remove
    add_items_combo(ui.ar_metajob_metajob, r.MetaJobs)
    add_items_combo(ui.ar_fluorophore_fluorophore, r.Fluorophores)
    add_items_combo(ui.ar_solvent_solvent, r.Solvents)

    # selective results -> ex
    with r.statusLoad(df='comp-ex') as df:
        solvents, fluorophores, states, metajobs, properties = extractIndices(df)
    add_items_list(ui.select_ex_metajobs, metajobs)
    add_items_list(ui.select_ex_states, states)
    add_items_list(ui.select_ex_properties, properties)

    # selective results -> em
    with r.statusLoad(df='comp-em') as df:
        solvents, fluorophores, states, metajobs, properties = extractIndices(df)
    add_items_list(ui.select_em_metajobs, metajobs)
    add_items_list(ui.select_em_states, states)
    add_items_list(ui.select_em_properties, properties)

    # selective results -> freq
    with r.statusLoad(df='comp-freq') as df:
        solvents, fluorophores, states, metajobs, properties = extractIndices(df)
    add_items_list(ui.select_freq_metajobs, metajobs)
    add_items_list(ui.select_freq_states, states)
    add_items_list(ui.select_freq_properties, properties)

    # selective results -> cas
    with r.statusLoad(df='comp-casscf') as df:
        solvents, fluorophores, states, metajobs, properties = extractIndices(df)
    add_items_list(ui.select_cas_metajobs, metajobs)
    add_items_list(ui.select_cas_states, states)
    add_items_list(ui.select_cas_properties, properties)

    # selective results -> pol
    with r.statusLoad(df='comp-pol') as df:
        solvents, fluorophores, states, metajobs, properties = extractIndices(df)
    add_items_list(ui.select_pol_metajobs, metajobs)
    add_items_list(ui.select_pol_states, states)
    add_items_list(ui.select_pol_properties, properties)

def setup_progress(ui: Ui, total: int) -> None:
    ui.general_progressBar.setValue(0)
    ui.general_progressBar.setMaximum(total)
    ui.general_progressBar_label.setText('0%')

def update_progress(ui: Ui, step: int) -> None:
    ui.general_progressBar.setValue(step)
    perc = (step/ui.general_progressBar.maximum())*100
    ui.general_progressBar_label.setText(f'{perc:.0f}%')

def update_status(ui: Ui, status: str) -> None:
    ui.statusBar().showMessage(status)

def threaded_viewAndPull(ui: Ui) -> None:
    ui.threadpool = QThreadPool()
    ui.runner = Runner(ui)

    ui.runner.signals.setup.connect(partial(setup_progress, ui))
    ui.runner.signals.progress.connect(partial(update_progress, ui))
    ui.runner.signals.status.connect(partial(update_status, ui))
    ui.runner.signals.finished.connect(partial(thread_finished, ui))
    ui.runner.signals.cancelled.connect(partial(thread_cancelled, ui))
    ui.runner.signals.socketError.connect(partial(connection_error, ui))
    ui.general_cancel_button.clicked.connect(ui.runner.shutdown)

    ui.general_pull_button.setEnabled(False)
    ui.threadpool.start(ui.runner)

def disconnect_signals(ui: Ui) -> None:
    ui.runner.signals.setup.disconnect()
    ui.runner.signals.progress.disconnect()
    ui.runner.signals.status.disconnect()
    ui.runner.signals.finished.disconnect()
    ui.runner.signals.cancelled.disconnect()
    ui.runner.signals.socketError.disconnect()

def connection_error(ui: Ui) -> None:
    QMessageBox(icon=QMessageBox.Icon.Critical, text='Could not connect to cluster!').exec()

def thread_finished(ui: Ui) -> None:
    ui.general_output.clear()
    if ui.general_show.isChecked():
        prettyDisplay(ui)
    ui.statusBar().showMessage("Finished")
    ui.general_pull_button.setEnabled(True)
    disconnect_signals(ui)

def thread_cancelled(ui: Ui) -> None:
    ui.statusBar().showMessage("Cancelled")
    ui.general_pull_button.setEnabled(True)
    disconnect_signals(ui)

def connect(ui: Ui) -> None:
    ui.general_to_button.clicked.connect(partial(timedOut, ui))
    ui.general_visds_button.clicked.connect(partial(visualise_ds, ui))
    ui.general_solvent_button.clicked.connect(partial(viewSolvents, ui))
    ui.general_view_button.clicked.connect(partial(prettyDisplay, ui))

    ui.general_pull_button.clicked.connect(partial(threaded_viewAndPull, ui))
    ui.general_reset_button.clicked.connect(partial(reset_window, ui))

    ui.select_ex_button.clicked.connect(partial(printDBSelection, ui, 'comp-ex'))
    ui.select_em_button.clicked.connect(partial(printDBSelection, ui, 'comp-em'))
    ui.select_freq_button.clicked.connect(partial(printDBSelection, ui, 'comp-freq'))
    ui.select_cas_button.clicked.connect(partial(printDBSelection, ui, 'comp-casscf'))
    ui.select_pol_button.clicked.connect(partial(printDBSelection, ui, 'comp-pol'))

    ui.ar_metajob_add.clicked.connect(partial(add_metajob, ui))
    ui.ar_metajob_remove.clicked.connect(partial(rem_metajob, ui))
    ui.ar_fluorophore_add.clicked.connect(partial(add_fluorophore, ui))
    ui.ar_fluorophore_remove.clicked.connect(partial(rem_fluorophore, ui))
    ui.ar_solvent_add.clicked.connect(partial(add_solvent, ui))
    ui.ar_solvent_remove.clicked.connect(partial(rem_solvent, ui))



if __name__ == '__main__':
    app = QApplication(sys.argv)
    ui = Ui()
    app.setWindowIcon(qta.icon('fa5s.table'))
    ui.threadpool = QThreadPool()
    populate(ui)
    connect(ui)

    sys.exit(app.exec())
