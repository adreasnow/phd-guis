import sys
import pathlib
import resources as r
from pandas import DataFrame
from functools import partial
from PyQt6.QtCore import QRunnable, pyqtSlot, pyqtSignal, QObject, QThreadPool
from PyQt6 import uic
from PyQt6.QtWidgets import QMainWindow, QListWidget, QListWidgetItem, QComboBox, QApplication
import qtawesome as qta

class Ui(QMainWindow):
    def __init__(self):
        super(Ui, self).__init__()
        uic.loadUi(f'{pathlib.Path(__file__).parent.resolve()}/metajobBuilder.ui', self)
        self.show()

def extractIndices(df: DataFrame) -> list[float]:
    levels = len(df.index[0])
    indexLists = [[] for i in range(levels)]
    for row in df.index:
        for count, level in enumerate(row):
            if level not in indexLists[count]:
                indexLists[count] += [level]
    return [df.columns.to_list()] + indexLists


class WorkerSignals(QObject):
    setup = pyqtSignal(int)
    output = pyqtSignal(str)
    shutdown = pyqtSignal()
    setup = pyqtSignal(int)
    step = pyqtSignal()
    finished = pyqtSignal()

class Runner(QRunnable):
    signals = WorkerSignals()

    def __init__(self, ui_in):
        super().__init__()
        self.ui = ui_in
        self.shutdownCheck = False

    @pyqtSlot()
    def run(self) -> None:
        self.submit()
        if self.shutdownCheck:
            self.signals.shutdown.emit()
        else:
            self.signals.finished.emit()

    def shutdown(self) -> None:
        self.shutdownCheck = True

    def submit(self) -> None:
        config = r.loadConfig()
        if self.ui.m3_button.isChecked():
            unloaded_cluster = r.clusters.m3
        elif self.ui.monarch_button.isChecked():
            unloaded_cluster = r.clusters.monarch
        elif self.ui.gadi_button.isChecked():
            unloaded_cluster = r.clusters.gadi

        cluster = r.loadRemotes(unloaded_cluster)

        with r.clusterHandler(unloaded_cluster) as clu:
            with r.statusLoad(df='progress') as df:
                _, _, states, _ = extractIndices(df)
                metajob = self.ui.jobType_widg.currentData()
                states = [i.data(1) for i in self.ui.stateList_widg.selectedItems()]
                if not metajob.gs:
                    try:
                        states.remove(r.States.s0)
                        self.signals.output.emit(f'{r.States.s0} not logical with {metajob}')
                    except ValueError:
                        pass
                if not metajob.es:
                    try:
                        states.remove(r.States.s1)
                        self.signals.output.emit(f'{r.States.s1} not logical with {metajob}')
                    except ValueError:
                        pass
                    try:
                        states.remove(r.States.s2)
                        self.signals.output.emit(f'{r.States.s2} not logical with {metajob}')
                    except ValueError:
                        pass
                progressSteps = len(states)*len([i.data(1) for i in self.ui.fluorophoreList_widg.selectedItems()])*len([i.data(1) for i in self.ui.solventList_widg.selectedItems()])                
                self.signals.setup.emit(progressSteps)
                for state in states:
                    for fluorophore in [i.data(1) for i in self.ui.fluorophoreList_widg.selectedItems()]:
                        for solvent in [i.data(1) for i in self.ui.solventList_widg.selectedItems()]:
                            if self.shutdownCheck:
                                self.signals.shutdown.emit()
                                return
                            if (fluorophore.gas) and (not fluorophore.revised) and (solvent != r.Solvents.gas):
                                pass
                            else:
                                if (solvent != r.Solvents.gas) and (metajob.gasonly):
                                    self.signals.output.emit(f'Metajob {metajob} cannot be used with solvent')
                                else:
                                    refSolvent = solvent if self.ui.refJobSolvent_widg.currentData() == 'Same as Main Job' else self.ui.refJobSolvent_widg.currentData()
                                    refState = state if self.ui.refJobState_widg.currentData() == 'Same as Main Job' else self.ui.refJobState_widg.currentData()
                                    status = df.at[(fluorophore, state, metajob), solvent]
                                    refStatus = df.at[(fluorophore, refState, self.ui.refJobType_widg.currentData()), refSolvent]
                                    if refStatus == r.Status.finished or self.ui.force_widg.isChecked():
                                        if status != r.Status.finished or self.ui.resubmit_widg.isChecked():
                                            if metajob.job == r.Jobs.esd:
                                                refState = r.States.s0
                                            refJob = r.Job.from_MetaJob(self.ui.refJobType_widg.currentData(), fluorophore, refSolvent, refState, cluster=cluster)
                                            if self.ui.orca_freqIn_widg.isChecked():
                                                freqJob = r.MetaJobs.or_wb_freq
                                                jobRefJob = r.Job.from_MetaJob(freqJob, fluorophore, refSolvent, refState, cluster=cluster)
                                            else:
                                                jobRefJob = refJob
                                            if (metajob.job == r.Jobs.esd and state == r.States.s0):
                                                esdState = self.ui.orca_esd_es_widg.currentData()
                                            else:
                                                esdState = r.States.s0

                                            job = r.Job.from_MetaJob(metajob, fluorophore, solvent, state, catxyzpath=refJob.xyzfile, submit=self.ui.submit_widg.isChecked(),
                                                                     partner=self.ui.partner_widg.isChecked(), procs=self.ui.cores_widg.value(),
                                                                     mem=self.ui.memory_widg.value(), time=(self.ui.time_widg.value()*24), cluster=cluster,
                                                                     # ORCA Specific
                                                                     kdiis=self.ui.orca_kdiis_widg.isChecked(), soscf=self.ui.orca_soscf_widg.isChecked(), restart=self.ui.restart_widg.isChecked(),
                                                                     notrah=self.ui.orca_notrah_widg.isChecked(), scfstring=self.ui.orca_scfstring_widg.text(), refJob=jobRefJob,
                                                                     verytightopt=self.ui.orca_vtightopt_widg.isChecked(), orbstep=self.ui.orca_orbstep_widg.currentText(),
                                                                     switchstep=self.ui.orca_switchstep_widg.currentText(), switchconv=self.ui.orca_switchconv_widg.value(), inhess=self.ui.orca_freqIn_widg.isChecked(),
                                                                     calchess=self.ui.orca_calchess_widg.isChecked(), recalchess=self.ui.orca_recalchess_widg.value(), esdState=esdState)
                                            if metajob.job in [r.Jobs.esd]:
                                                if state == r.States.s0:
                                                    job.esdLowerJob = r.Job.from_MetaJob(self.ui.orca_esd_job_widg.currentData(), fluorophore, solvent, r.States.s0, cluster=cluster)
                                                    job.esdHigherJob = r.Job.from_MetaJob(self.ui.orca_esd_job_widg.currentData(), fluorophore, solvent, self.ui.orca_esd_es_widg.currentData(), cluster=cluster)
                                                else:
                                                    job.esdLowerJob = r.Job.from_MetaJob(self.ui.orca_esd_job_widg.currentData(), fluorophore, solvent, r.States.s0, cluster=cluster)
                                                    job.esdHigherJob = r.Job.from_MetaJob(self.ui.orca_esd_job_widg.currentData(), fluorophore, solvent, state, cluster=cluster)

                                            if self.ui.orca_mo_widg.isChecked():
                                                orca_mo_refSolvent = solvent if self.ui.orca_mo_refJobSolvent_widg.currentData() == 'Same as Main Job' else self.ui.orca_mo_refJobSolvent_widg.currentData()
                                                orca_mo_refState = state if self.ui.orca_mo_refJobState_widg.currentData() == 'Same as Main Job' else self.ui.orca_mo_refJobState_widg.currentData()
                                                mo_ref_job = r.Job.from_MetaJob(self.ui.orca_mo_refJobType_widg.currentData(), fluorophore, orca_mo_refSolvent, orca_mo_refState, cluster=cluster)
                                                job.mopath = f'{mo_ref_job.path}/{mo_ref_job.name}/{mo_ref_job.name}.gbw'

                                            if job.method.rank == r.Methods.Rank.cas and state == r.States.s0:
                                                job.perturbedRoots == job.nroots
                                            output = clu.buildJob(job)
                                            if type(output) == list:
                                                self.signals.output.emit('\n'.join(output))
                                            elif type(output) == str:
                                                self.signals.output.emit(output)


                                            if self.ui.submit_widg.isChecked() or self.ui.resubmit_widg.isChecked():
                                                df.at[(fluorophore, state, metajob), solvent] = r.Status.queued
                                        else:
                                            self.signals.output.emit(f'{metajob} of state {state} of {fluorophore} in {solvent} already finished')
                                    else:
                                        self.signals.output.emit(f'Reference job: {self.ui.refJobType_widg.currentData()} of state {refState} of {fluorophore} in {refSolvent} not finished')
                            self.signals.step.emit()

def add_items_list(widget: QListWidget, items: list[object]) -> None:
    for i in items:
        item_to_add = QListWidgetItem()
        item_to_add.setText(str(i))
        item_to_add.setData(1, i)
        widget.addItem(item_to_add)

def add_items_combo(widget: QComboBox, items: list[object]) -> None:
    for i in items:
        widget.addItem(str(i), userData=i)

def shutdown(ui: Ui) -> None:
    ui.statusBar().showMessage("Cancelled")
    ui.build_button.setEnabled(True)
    disconnect_signals(ui)

def to_output(ui: Ui, output: str) -> None:
    ui.output.setPlainText(ui.output.toPlainText() + output + '\n')
    ui.output.verticalScrollBar().setValue(ui.output.verticalScrollBar().maximum())

def setup_progress(ui: Ui, total: int) -> None:
    ui.progressBar.setValue(0)
    ui.progressBar.setMaximum(total)
    ui.progressBar_label.setText('0%')

def update_progress(ui: Ui) -> None:
    ui.progressBar.setValue(ui.progressBar.value() + 1)
    perc = (ui.progressBar.value()/ui.progressBar.maximum())*100
    ui.progressBar_label.setText(f' {perc:.0f}%')

def thread_finished(ui: Ui) -> None:
    ui.statusBar().showMessage("Finished")  
    ui.build_button.setEnabled(True)
    disconnect_signals(ui)

def disconnect_signals(ui: Ui) -> None:
    ui.runner.signals.setup.disconnect()
    ui.runner.signals.output.disconnect()
    ui.runner.signals.step.disconnect()
    ui.runner.signals.finished.disconnect()
    ui.runner.signals.shutdown.disconnect()

def run_thread(ui: Ui) -> None:
    ui.threadpool = QThreadPool()
    ui.runner = Runner(ui)
    ui.output.clear()
    ui.runner.signals.setup.connect(partial(setup_progress, ui))
    ui.runner.signals.output.connect(partial(to_output, ui))
    ui.runner.signals.step.connect(partial(update_progress, ui))
    ui.runner.signals.finished.connect(partial(thread_finished, ui))
    ui.runner.signals.shutdown.connect(partial(shutdown, ui))
    ui.cancel_button.clicked.connect(ui.runner.shutdown)

    ui.statusBar().showMessage("Running...")
    ui.build_button.setEnabled(False)
    ui.threadpool.start(ui.runner)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ui = Ui()
    app.setWindowIcon(qta.icon('fa5s.tasks'))
    with r.statusLoad(df='progress') as df:
        solvents, fluorophores, states, metajobs = extractIndices(df)

    # Populate options
    add_items_list(ui.fluorophoreList_widg, fluorophores)
    add_items_list(ui.solventList_widg, solvents)
    add_items_list(ui.stateList_widg, states)
    add_items_combo(ui.jobType_widg, metajobs)
    ui.jobType_widg.setCurrentIndex(3)

    add_items_combo(ui.refJobType_widg, metajobs)
    ui.refJobType_widg.setCurrentIndex(0)
    ui.refJobState_widg.addItem('Same as Main Job', userData='Same as Main Job')
    add_items_combo(ui.refJobState_widg, states)
    ui.refJobSolvent_widg.addItem('Same as Main Job', userData='Same as Main Job')
    add_items_combo(ui.refJobSolvent_widg, solvents)

    add_items_combo(ui.orca_mo_refJobType_widg, metajobs)
    ui.orca_mo_refJobState_widg.addItem('Same as Main Job', userData='Same as Main Job')
    add_items_combo(ui.orca_mo_refJobState_widg, states)
    ui.orca_mo_refJobSolvent_widg.addItem('Same as Main Job', userData='Same as Main Job')
    add_items_combo(ui.orca_mo_refJobSolvent_widg, solvents)

    add_items_combo(ui.orca_esd_job_widg, [i for i in metajobs if i.job in [r.Jobs.freq, r.Jobs.casscfFreq] and i.software == r.Software.orca])
    add_items_combo(ui.orca_esd_es_widg, states)

    ui.orca_orbstep_widg.addItems(['SuperCI_PT (default)', 'SuperCI', 'DIIS', 'KDIIS', 'SOSCF', 'NR'])
    ui.orca_orbstep_widg.setCurrentIndex(1)
    ui.orca_switchstep_widg.addItems(['SuperCI_PT (default)', 'SuperCI', 'DIIS', 'KDIIS', 'SOSCF', 'NR'])
    ui.orca_switchstep_widg.setCurrentIndex(2)


    ui.build_button.clicked.connect(partial(run_thread, ui))

    sys.exit(app.exec())
