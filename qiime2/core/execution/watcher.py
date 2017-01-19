"""
THIS IS DEFUNCT

We are going to use dask.distributed instead to manage scheduling.
"""



import threading

class Watcher(threading.Thread):
    TIMEOUT = 50

    def __init__(self):
        super().__init__(daemon=True)
        self.stopped = threading.Event()

    def run(self):
        if self.blocking:
            self.block()

        else:
            while not self.stopped.wait(self.TIMEOUT):
                if self.poll():
                    self.stopped.set()



class SubmitJob:
    pass





class SUBMIT(SubmitJob, blocking=False):
    def submit(self, input):
        pass

    def ping(self, id):
        pass




class SubmitSubprocess(SubmitJob, blocking=True):
    def submit(self, input):
        pass


class TorqueSubmitter(Submitter):
    queue = Submitter.Configurable(str, required=True)
    max_walltime = Submitter.Configurable(int, required=False, default=100)

    def submit(self, input):
        pass

"""
[ExecutionContext]
    [Host]
    type: local
    checkpoint_dir: ~/.qiime2/checkpoints/
    working_dir: /tmp/

    [Submitter]
    type: SubprocessSubmitter
    pool_size: 3


"""

"""
execution_context:

    host:
        type: ssh
        hostname: monsoon.hpc.nau.edu
        checkpoint_dir: /scratch/etb36/qiime2/checkpoints/
        working_dir: /scratch/etb36/qiime2/working/
        authentication:
            user: etb36
            password: whoatherebuddy
        prelude:
            - module load anaconda
            - source activate qiime2

    submitter:
        type: qiime2.SlurmSubmitter
        partition: HighMem
        max_walltime: 10000
        pool_size: 10

    subcontexts:
        plugin_name.foo:
            host:
                type: local
                checkpoint_dir: ~/.qiime2/checkpoints/
                working_dir: /tmp/
            submitter:
                type: qiime2.SubprocessSubmitter
                pool_size: 3

        other_plugin.bar:
            submitter:
                pool_size: 100
"""
