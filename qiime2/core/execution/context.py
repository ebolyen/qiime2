class ExecutionContext:

    def __init__(self, client: 'distributed.Client'):
        self._client = client

    def _destructure_arg(self, arg):
        if isinstance(arg, ScheduledResult):
            return arg._proxy_
        return arg

    def schedule(self, plugin, name, *args, **kwargs):
        destructored_args = [self._destructure_arg(a) for a in args]
        destructored_kwargs = \
            {k: self._destructure_arg(a) for k, a in kwargs.items()}

        # As written, this won't work well, as the delayed dask-graph isn't
        # particularly easy to parse. It should be an action graph that is generated instead
        return ScheduledResultCollection(delayed(action)(*args, **kwargs))

    def _collect_(self, result):
        r = self._submit(result)
        while not r.ready():
            self._sleep()

        return Result.load(r.path)

    def __call__(self, pipeline, **kwargs):
        for result in pipeline(self, **kwargs):
            self._submit(result)

    def _submit(self, result):
        pass


    def _sleep(self):
        pass
