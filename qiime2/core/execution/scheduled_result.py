from abc import ABCMeta, abstractmethod


class ResultCollectionBase(metaclass=ABCMeta):

    @abstractmethod
    def __len__(self):
        raise NotImplementedError

    @abstractmethod
    def __iter__(self):
        raise NotImplementedError

    @abstractmethod
    def __getitem__(self, indexable) -> ResultBase:
        raise NotImplementedError

    @abstractmethod
    def keys(self):
        raise NotImplementedError

    @abstractmethod
    def values(self):
        raise NotImplementedError

    @abstractmethod
    def items(self):
        raise NotImplementedError



class ScheduledResultCollection(ResultCollectionBase):

    def __init__(self, ctx, delayed: 'dask.delayed'):
        self._ctx
        self._delayed = delayed

        self._results = OrderedDict()
        self._signature = delayed.dask[delayed.key][0].signature


    def __iter__(self):
        pass

    def __getitem__(self, name):
        pass


class ScheduledResult:
    def __init__(self, ctx, ):
        self._ctx = ctx
        self.name = name
        self.inputs = inputs
        self.action = action

    @property
    def inputs(self):
        return {}


    @property
    def action(self):
        return "plugin:action"

    def collect(self):
        self._ctx.collect(self)
