# ----------------------------------------------------------------------------
# Copyright (c) 2016--, QIIME 2 development team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
# ----------------------------------------------------------------------------

import abc
import concurrent.futures
import inspect
import os.path
import tempfile

import decorator

import qiime.sdk
import qiime.core.type as qtype
import qiime.core.archive as archive
from qiime.core.util import LateBindingAttribute, DropFirstParameter, tuplize


class Action(metaclass=abc.ABCMeta):
    type = 'action'
    # Whether to convert artifacts into a particular view ahead of time.
    view_conversion = True

    __call__ = LateBindingAttribute('_dynamic_call')
    async = LateBindingAttribute('_dynamic_async')

    # Converts a callable's signature into its wrapper's signature (i.e.
    # converts the "view API" signature into the "artifact API" signature).
    # Accepts a callable as input and returns a callable as output with
    # converted signature.
    @abc.abstractmethod
    def _callable_sig_converter_(self, callable):
        raise NotImplementedError

    # Executes a callable on the provided `view_args`, wrapping and returning
    # the callable's outputs. In other words, executes the "view API", wrapping
    # and returning the outputs as the "artifact API". `view_args` is a dict
    # mapping parameter name to unwrapped value (i.e. view). `view_args`
    # contains an entry for each parameter accepted by the wrapper. It is the
    # executor's responsibility to perform any additional transformations on
    # these parameters, or provide extra parameters, in order to execute the
    # callable. `output_types` is an OrderedDict mapping output name to QIIME
    # type (e.g. semantic type).
    @abc.abstractmethod
    def _callable_executor_(self, callable, view_args, output_types):
        raise NotImplementedError

    # Private constructor
    @classmethod
    def _init(cls, callable, signature, package, name, description):
        """

        Parameters
        ----------
        callable : callable
        signature : qiime.core.type.Signature
        package : str
        name : str
            Human-readable name for this action.
        description : str
            Human-readable description for this action.

        """
        self = cls.__new__(cls)
        self.__init(callable, signature, package, name, description)
        return self

    # This "extra private" constructor is necessary because `Action` objects
    # can be initialized from a static (classmethod) context or on an
    # existing instance (see `_init` and `__setstate__`, respectively).
    def __init(self, callable, signature, package, name, description,
               pid=None):
        self._callable = callable
        self.signature = signature
        self.package = package
        self.name = name
        self.description = description

        self.id = callable.__name__
        if pid is None:
            pid = os.getpid()
        self._pid = pid

        self._dynamic_call = self._get_callable_wrapper()
        self._dynamic_async = self._get_async_wrapper()

    def __init__(self):
        raise NotImplementedError(
            "%s constructor is private." % self.__class__.__name__)

    @property
    def source(self):
        """

        Returns
        -------
        str
            The source code of this action's callable formatted as Markdown
            text.

        """
        try:
            source = inspect.getsource(self._callable)
        except OSError:
            raise TypeError(
                "Cannot retrieve source code for callable %r" %
                self._callable.__name__)
        return markdown_source_template % {'source': source}

    def get_import_path(self):
        return self.package + '.' + self.id

    def __repr__(self):
        return "<%s %s>" % (self.type, self.get_import_path())

    def __getstate__(self):
        return {
            'callable': self._callable,
            'signature': self.signature,
            'package': self.package,
            'name': self.name,
            'description': self.description,
            'pid': self._pid
        }

    def __setstate__(self, state):
        self.__init(**state)

    def _get_callable_wrapper(self):
        def callable_wrapper(*args, **kwargs):
            provenance = archive.ActionProvenanceCapture(
                self.type, self.package, self.id)
            # This function's signature is rewritten below using
            # `decorator.decorator`. When the signature is rewritten, args[0]
            # is the function whose signature was used to rewrite this
            # function's signature.
            args = args[1:]

            # TODO this may be able to be simplified once Signature respects
            # order.
            wrapper_sig = self._callable_sig_converter_(self._callable)
            wrapper_sig = inspect.Signature.from_callable(wrapper_sig)
            wrapper_params = wrapper_sig.parameters

            user_input = {name: value for value, name in
                          zip(args, wrapper_params)}
            user_input.update(kwargs)

            self.signature.check_types(**user_input)
            output_types = self.signature.solve_output(**user_input)

            artifacts = {}
            for name in self.signature.inputs:
                artifact = artifacts[name] = user_input[name]
                provenance.add_input(name, artifact)

            parameters = {}
            for name, (primitive_type, _) in self.signature.parameters.items():
                parameter = parameters[name] = user_input[name]
                provenance.add_parameter(name, primitive_type, parameter)

            view_args = parameters.copy()
            if self.view_conversion:
                for name, (_, view_type) in self.signature.inputs.items():
                    recorder = provenance.transformation_recorder(name)
                    view_args[name] = artifacts[name]._view(view_type,
                                                            recorder)
            else:
                view_args.update(artifacts)

            outputs = self._callable_executor_(self._callable, view_args,
                                               output_types, provenance)
            # `outputs` matches a Python function's return: either a single
            # value is returned, or it is a tuple of return values. Treat both
            # cases uniformly.
            outputs_tuple = tuplize(outputs)
            for output in outputs_tuple:
                output._orphan(self._pid)

            if len(outputs_tuple) != len(self.signature.outputs):
                raise ValueError(
                    "Number of callable outputs must match number of outputs "
                    "defined in signature: %d != %d" %
                    (len(outputs_tuple), len(self.signature.outputs)))

            # Wrap in a Results object mapping output name to value so users
            # have access to outputs by name or position.
            return qiime.sdk.Results(self.signature.outputs.keys(),
                                     outputs_tuple)

        callable_wrapper = self._rewrite_wrapper_signature(callable_wrapper)
        self._set_wrapper_properties(callable_wrapper, '__call__')
        return callable_wrapper

    def _get_async_wrapper(self):
        def async_wrapper(*args, **kwargs):
            # TODO handle this better in the future, but stop the massive error
            # caused by MacOSX async runs for now.
            try:
                import matplotlib as plt
                if plt.rcParams['backend'] == 'MacOSX':
                    raise EnvironmentError(backend_error_template %
                                           plt.matplotlib_fname())
            except ImportError:
                pass

            # This function's signature is rewritten below using
            # `decorator.decorator`. When the signature is rewritten, args[0]
            # is the function whose signature was used to rewrite this
            # function's signature.
            args = args[1:]

            pool = concurrent.futures.ProcessPoolExecutor(max_workers=1)
            future = pool.submit(self, *args, **kwargs)
            pool.shutdown(wait=False)
            return future

        async_wrapper = self._rewrite_wrapper_signature(async_wrapper)
        self._set_wrapper_properties(async_wrapper, 'async')
        return async_wrapper

    def _rewrite_wrapper_signature(self, wrapper):
        # Convert the callable's signature into the wrapper's signature and set
        # it on the wrapper.
        return decorator.decorator(
            wrapper, self._callable_sig_converter_(self._callable))

    def _set_wrapper_properties(self, wrapper, name):
        wrapper.__name__ = wrapper.__qualname__ = name
        wrapper.__module__ = self.package
        del wrapper.__annotations__
        # This is necessary so that `inspect` doesn't display the wrapped
        # function's annotations (the annotations apply to the "view API" and
        # not the "artifact API").
        del wrapper.__wrapped__


class Method(Action):
    type = 'method'

    # Abstract method implementations:

    def _callable_sig_converter_(self, callable):
        # No conversion necessary.
        return callable

    def _callable_executor_(self, callable, view_args, output_types,
                            provenance):
        output_views = callable(**view_args)
        output_views = tuplize(output_views)

        # TODO this won't work if the user has annotated their "view API" to
        # return a `typing.Tuple` with some number of components. Python will
        # return a tuple when there are multiple return values, and this length
        # check will fail because the tuple as a whole should be matched up to
        # a single output type instead of its components. This is an edgecase
        # due to how Python handles multiple returns, and can be worked around
        # by using something like `typing.List` instead.
        if len(output_views) != len(output_types):
            raise TypeError(
                "Number of output views must match number of output "
                "semantic types: %d != %d"
                % (len(output_views), len(output_types)))

        output_artifacts = []
        for output_view, (semantic_type, view_type) in \
                zip(output_views, output_types.values()):
            if type(output_view) is not view_type:
                raise TypeError(
                    "Expected output view type %r, received %r" %
                    (view_type.__name__, type(output_view).__name__))
            artifact = qiime.sdk.Artifact._from_view(
                semantic_type, output_view, view_type, provenance.fork())
            output_artifacts.append(artifact)

        if len(output_artifacts) == 1:
            return output_artifacts[0]
        else:
            return tuple(output_artifacts)

    @classmethod
    def _init(cls, callable, inputs, parameters, outputs, package, name,
              description):
        signature = qtype.MethodSignature(callable, inputs, parameters,
                                          outputs)
        return super()._init(callable, signature, package, name, description)


class Visualizer(Action):
    type = 'visualizer'

    # Abstract method implementations:

    def _callable_sig_converter_(self, callable):
        return DropFirstParameter.from_function(callable)

    def _callable_executor_(self, callable, view_args, output_types,
                            provenance):
        # TODO use qiime.plugin.OutPath when it exists, and update visualizers
        # to work with OutPath instead of str. Visualization._from_data_dir
        # will also need to be updated to support OutPath instead of str.
        with tempfile.TemporaryDirectory(prefix='qiime2-temp-') as temp_dir:
            ret_val = callable(output_dir=temp_dir, **view_args)
            if ret_val is not None:
                raise TypeError(
                    "Visualizer %r should not return anything. "
                    "Received %r as a return value." % (self, ret_val))
            return qiime.sdk.Visualization._from_data_dir(temp_dir, provenance)

    @classmethod
    def _init(cls, callable, inputs, parameters, package, name, description):
        signature = qtype.VisualizerSignature(callable, inputs, parameters)
        return super()._init(callable, signature, package, name, description)


class Pipeline(Action):
    type = 'pipeline'
    view_conversion = False

    # Abstract method implementations:


markdown_source_template = """
```python
%(source)s
```
"""

# TODO add unit test for callables raising this
backend_error_template = """
Your current matplotlib backend (MacOSX) does not work with async calls.
A recommended backend is Agg, and can be changed by modifying your
matplotlibrc "backend" parameter, which can be found at: \n\n %s
"""
