class ResultCollection:

    def __init__(self, ordered_scheduled_results):
        pass

    @property
    def status(self):
        pass

    def __len__(self):
        return len(self._results)

    def __iter__(self):
        for r in self._results.values():
            yield r.collect()

    def __getitem__(self, indexable) -> Result:
        if isinstance(indexable, str):
            return self._results[indexable].collect()

        for idx, r in enumerate(self._results.values()):
            if idx == indexable:
                return r.collect()

        raise KeyError()

    def wait(self):
        for r in self._results.values():
            _ = r.collect()

        return self

    def on(self, event, callback):
        pass


    def to_token(self, password=None):
        pass

    @classmethod
    def from_token(cls, token_string, password=None):
        pass
