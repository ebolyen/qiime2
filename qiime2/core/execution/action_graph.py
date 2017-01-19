class ActionGraph:
    """Describe a series of actions

    This is necessary because dask.deferred stores keyword arguments as an
    partial application of a dictionary and the function, which is relatively
    awkward to inspect.

    This object should support comparison to allow instances of ctx.schedule
    and the provenance of an existing artifact to be compared. Ideally this
    would be relative to a specific UUID which will make the comparison cheaper
    """

    @staticmethod
    def _node_match(a, b):
        return a == b

    @staticmethod
    def _edge_match(a, b):
        return a == b


    def __init__(self, plugin_name, action_name, **kwargs):
        pass



    def __eq__(self, other):
        return self.graph.is_isomorphic(
            other.graph,
            node_match=ActionGraph._node_match,
            edge_match=ActionGraph._edge_match)

    def __ne__(self, other):
        return not self == other

    def to_delayed(*given):
        pass
