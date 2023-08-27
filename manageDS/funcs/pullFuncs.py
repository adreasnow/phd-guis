import resources as r
from copy import deepcopy
from .generalFuncs import extractIndices
from PyQt6.QtCore import QRunnable, pyqtSlot, pyqtSignal, QObject
from socket import gaierror

class WorkerSignals(QObject):
    setup = pyqtSignal(int)
    progress = pyqtSignal(int)
    status = pyqtSignal(str)
    finished = pyqtSignal()
    cancelled = pyqtSignal()
    socketError = pyqtSignal()

class Runner(QRunnable):
    signals = WorkerSignals()

    def __init__(self, ui):
        super().__init__()
        self.ui = ui
        self.shutdownCheck = False

    @pyqtSlot()
    def run(self) -> None:
        self.check_progress()
        if self.shutdownCheck:
            self.signals.cancelled.emit()
        else:
            self.signals.status.emit('Pulling Results')
            self.pull_results()
            self.signals.finished.emit()

    def shutdown(self) -> None:
        self.shutdownCheck = True

    def check_progress(self) -> None:
        clusters = []
        if self.ui.general_monarch.isChecked():
            clusters += [r.clusters.monarch]
        if self.ui.general_m3.isChecked():
            clusters += [r.clusters.m3]
        if self.ui.general_gadi.isChecked():
            clusters += [r.clusters.gadi]

        stateList = []
        if self.ui.general_s0.isChecked():
            stateList += [r.States.s0]
        if self.ui.general_s1.isChecked():
            stateList += [r.States.s1]
        if self.ui.general_s2.isChecked():
            stateList += [r.States.s2]

        if self.ui.general_progress.isChecked():
            with r.statusLoad(df='progress') as df:
                solvents, fluorophores, states, metajobs = extractIndices(df)
                for cluster_choice in clusters:
                    try:
                        with r.clusterHandler(cluster_choice) as clu:
                            jobList = []
                            cluster = r.loadRemotes(cluster_choice)
                            metajobs = [i.data(1) for i in self.ui.general_metajobs.selectedItems()]
                            for metajob in metajobs:
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
                                    if state == r.States.s2:
                                        fluorophores = [fluorophore for fluorophore in r.Fluorophores if (fluorophore.root == r.States.s2 and bool(fluorophore))]
                                    else:
                                        _, fluorophores, _, _ = extractIndices(df)
                                    for fluorophore in fluorophores:
                                        solventList = [r.Solvents.gas] if metajob.gasonly else solvents + [r.Solvents.gas]
                                        for solvent in solventList:
                                            if (self.ui.general_gas.isChecked() and solvent == r.Solvents.gas) or not self.ui.general_gas.isChecked():
                                                if (fluorophore.gas) and (not fluorophore.revised) and (solvent != r.Solvents.gas):
                                                    pass
                                                else:
                                                    jobList += [(fluorophore, state, metajob, solvent)]

                            self.signals.setup.emit(len(jobList))
                            for count, (fluorophore, state, metajob, solvent) in enumerate(jobList):
                                count += 1
                                if self.shutdownCheck:
                                    return
                                self.signals.status.emit(f'Checking {metajob} of {state} {fluorophore} in {solvent} from {cluster.cluster}')
                                self.signals.progress.emit(count)
                                status = df.at[(fluorophore, state, metajob), solvent]
                                if (status != r.Status.finished) or self.ui.general_full.isChecked():
                                    job = r.Job.from_MetaJob(metajob, fluorophore, solvent, state, cluster=cluster)
                                    status = clu.checkJobStatus(job)
                                    if self.ui.general_reset.isChecked() or status != None:
                                        df.at[(fluorophore, state, metajob), solvent] = status
                    except gaierror:
                        self.signals.socketError.emit()
                        self.shutdownCheck = True
                        return


    def pull_results(self) -> None:
        clusters = []
        if self.ui.general_monarch.isChecked():
            clusters += [r.clusters.monarch]
        if self.ui.general_m3.isChecked():
            clusters += [r.clusters.m3]
        if self.ui.general_gadi.isChecked():
            clusters += [r.clusters.gadi]

        stateList = []
        if self.ui.general_s0.isChecked():
            stateList += [r.States.s0]
        if self.ui.general_s1.isChecked():
            stateList += [r.States.s1]
        if self.ui.general_s2.isChecked():
            stateList += [r.States.s2]

        dfList = []
        if self.ui.general_cas.isChecked():
            dfList += ['comp-casscf']
        if self.ui.general_emission.isChecked():
            dfList += ['comp-em']
        if self.ui.general_excitation.isChecked():
            dfList += ['comp-ex']
        if self.ui.general_freq.isChecked():
            dfList += ['comp-freq']
        if self.ui.general_pol.isChecked():
            dfList += ['comp-pol']

        for dfName in dfList:
            with r.statusLoad(df=dfName) as df:
                with r.statusLoad(df="progress") as df_progress:
                    solvents, fluorophores, _, metajobs, properties = extractIndices(df)
                    for cluster_choice in clusters:
                        with r.clusterHandler(cluster_choice) as clu:
                            cluster = r.loadRemotes(cluster_choice)
                            for metajob in metajobs:
                                if metajob in [i.data(1) for i in self.ui.general_metajobs.selectedItems()]:
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
                                        if state == r.States.s2:
                                            fluorophores = [fluorophore for fluorophore in r.Fluorophores if (fluorophore.root == r.States.s2 and bool(fluorophore))]
                                        else:
                                            _, fluorophores, _, _, _ = extractIndices(df)
                                        for fluorophore in fluorophores:
                                            solventList = [r.Solvents.gas] if metajob.gasonly else solvents + [r.Solvents.gas]
                                            for solvent in solventList:
                                                if (self.ui.general_gas.isChecked() and solvent == r.Solvents.gas) or not self.ui.general_gas.isChecked():
                                                    if (fluorophore.gas) and (not fluorophore.revised) and (solvent != r.Solvents.gas):
                                                        pass
                                                    else:
                                                        if df_progress.at[(fluorophore, state, metajob), solvent] == r.Status.finished:
                                                            status = df.at[(fluorophore, state, metajob, properties[0]), solvent]
                                                            if status in [0.0, None] or status == None or self.ui.general_full.isChecked():
                                                                self.signals.status.emit(f'Pulling {metajob} of {state} {fluorophore} in {solvent} from {cluster.cluster}')
                                                                job = r.Job.from_MetaJob(metajob, fluorophore, solvent, state, cluster=cluster)
                                                                if dfName == 'comp-casscf':
                                                                    try:
                                                                        e, e_trans, f, t, m = clu.pullJobEnergy(job)
                                                                        df.at[(fluorophore, state, metajob, r.Energy.CASSCF.de), solvent] = e
                                                                        df.at[(fluorophore, state, metajob, r.Energy.CASSCF.m), solvent] = m

                                                                        for e_t, i in zip(e_trans, [i for i in r.Energy.CASSCF if 'e_s0' in i.name]):
                                                                            df.at[(fluorophore, state, metajob, i), solvent] = e_t

                                                                        for f_t, i in zip(f, [i for i in r.Energy.CASSCF if 'f_s0' in i.name]):
                                                                            df.at[(fluorophore, state, metajob, i), solvent] = f_t

                                                                        for t_t, i in zip(t, [i for i in r.Energy.CASSCF if 't_s0' in i.name]):
                                                                            df.at[(fluorophore, state, metajob, i), solvent] = t_t
                                                                    except TypeError:
                                                                        pass

                                                                if dfName == 'comp-pol':
                                                                    try:
                                                                        iso, diag, pol = clu.pullJobEnergy(job)
                                                                        df.at[(fluorophore, state, metajob, r.Energy.Polarisability.iso), solvent] = iso
                                                                        df.at[(fluorophore, state, metajob, r.Energy.Polarisability.pol), solvent] = pol
                                                                        df.at[(fluorophore, state, metajob, r.Energy.Polarisability.diag), solvent] = diag
                                                                    except TypeError:
                                                                        pass

                                                                if dfName == 'comp-ex':
                                                                    try:
                                                                        e, e_trans, f, t = clu.pullJobEnergy(job)
                                                                        df.at[(fluorophore, state, metajob, r.Energy.Excitation.de), solvent] = e

                                                                        for e_t, i in zip(e_trans, [i for i in r.Energy.Excitation if 'e_s0' in i.name]):
                                                                            df.at[(fluorophore, state, metajob, i), solvent] = e_t

                                                                        for f_t, i in zip(f, [i for i in r.Energy.Excitation if 'f_s0' in i.name]):
                                                                            df.at[(fluorophore, state, metajob, i), solvent] = f_t

                                                                        for t_t, i in zip(t, [i for i in r.Energy.Excitation if 't_s0' in i.name]):
                                                                            df.at[(fluorophore, state, metajob, i), solvent] = t_t
                                                                    except TypeError:
                                                                        pass

                                                                if dfName == 'comp-em':
                                                                    try:
                                                                        e, e_trans, f, t = clu.pullJobEnergy(job)
                                                                        df.at[(fluorophore, state, metajob, r.Energy.Emission.de), solvent] = e

                                                                        for e_t, i in zip(e_trans, [i for i in r.Energy.Emission if 'e_s' in i.name]):
                                                                            df.at[(fluorophore, state, metajob, i), solvent] = e_t

                                                                        for f_t, i in zip(f, [i for i in r.Energy.Emission if 'f_s' in i.name]):
                                                                            df.at[(fluorophore, state, metajob, i), solvent] = f_t

                                                                        for t_t, i in zip(t, [i for i in r.Energy.Emission if 't_s' in i.name]):
                                                                            df.at[(fluorophore, state, metajob, i), solvent] = t_t
                                                                    except TypeError:
                                                                        pass

                                                                if dfName == 'comp-freq':
                                                                    try:
                                                                        e, zpve, neg = clu.pullJobEnergy(job)
                                                                        df.at[(fluorophore, state, metajob, r.Energy.Freq.de), solvent] = e
                                                                        df.at[(fluorophore, state, metajob, r.Energy.Freq.zpve), solvent] = zpve
                                                                        df.at[(fluorophore, state, metajob, r.Energy.Freq.neg), solvent] = neg
                                                                    except TypeError:
                                                                        pass
