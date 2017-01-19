import threading


class Schrivener(threading.Thread):
    """Record completion to SQLite database.

    Callbacks running on the scheduling worker will be invoked on seperate
    threads by dask.distributed, so queues should be used to prevent
    race-conditions
    """

    def run(self):
        pass
