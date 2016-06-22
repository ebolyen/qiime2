# ----------------------------------------------------------------------------
# Copyright (c) 2016--, QIIME 2 development team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
# ----------------------------------------------------------------------------

import json
import numbers
import re
import collections.abc

from qiime.core.type.grammar import TypeExpression, CompositeType, Predicate
import qiime.metadata as metadata


def is_primitive_type(type_):
    return isinstance(type_, _PrimitiveBase)


def _symbolify(*args, **kwargs):
    """Used to bootstrap the primitive type classes.
    They don't have a factory like the semantic types do.

    """
    def decorator(cls):
        return cls(*args, **kwargs)
    return decorator


class _PrimitiveBase(TypeExpression):
    def __contains__(self, value):
        # TODO: Make this work correctly. It is stubbed as True as current
        # usage is through encode/decode, we will need this to work for
        # the Artifact API and predicates.
        return True

    def _validate_union_(self, other, handshake=False):
        # It is possible we may want this someday: `Int | Str`, but order of
        # encode/decode dispatch wouldn't be straight-forward.
        # Order of the declaration could indicate "MRO", but then equality
        # must consider Int | Str != Str | Int, which feels weird.
        raise TypeError("Cannot union primitive types.")

    def _validate_intersection_(self, other, handshake=False):
        # This literally makes no sense for primitives. Even less sense than
        # C's Union type (which is actually an intersection type...)
        raise TypeError("Cannot intersect primitive types.")

    def to_ast(self):
        ast = super().to_ast()
        ast['type'] = 'primitive'
        return ast


class _Primitive(_PrimitiveBase):
    def __init__(self, **kwargs):
        # Use class name to avoid duplicating the name twice
        super().__init__(self.__class__.__name__, **kwargs)

    def _validate_predicate_(self, predicate):
        super()._validate_predicate_(predicate)
        # _valid_predicates will be on the class obj of the primitives to
        # make defining them easy
        if not isinstance(predicate, tuple(self._valid_predicates)):
            raise TypeError("Cannot supply %r as a predicate to %r type,"
                            " permitted predicates: %r"
                            % (predicate, self, self._valid_predicates))

        for bound in predicate.iter_boundaries():
            if not self._is_element_(bound):
                raise TypeError()

    def _apply_predicate_(self, predicate):
        return self.__class__(fields=self.fields, predicate=predicate)

    def __contains__(self, value):
        return (self._is_element_(value) and
                ((not self.predicate) or value in self.predicate))

    def _is_element_(self, value):
        return False


class _Collection(CompositeType):
    def __init__(self, field_names):
        super().__init__(self.__class__.__name__, field_names)

    def _validate_field_(self, name, value):
        if not isinstance(value, _Primitive):
            if isinstance(value, _CollectionPrimitive):
                raise TypeError("Cannot nest collection types.")
            else:
                raise TypeError("Collection type (%r) must be provided"
                                " primitives as arguments to its fields,"
                                " not %r" % (self, value))

        super()._validate_field_(name, value)

    def _apply_fields_(self, fields):
        return _CollectionPrimitive(self._is_element_, self.encode,
                                    self.decode, self.name, fields=fields)


class _CollectionPrimitive(_PrimitiveBase):
    def __init__(self, is_member, encode, decode, *args, **kwargs):
        # TODO: This is a nasty hack
        self._encode = encode
        self._decode = decode
        self._is_member = is_member

        super().__init__(*args, **kwargs)

    def encode(self, value):
        return self._encode(self, value)

    def decode(self, string):
        return self._decode(self, string)

    def _is_element_(self, value):
        return self._is_member(self, value)

    def _validate_predicate_(self, predicate):
        raise TypeError("Predicates cannot be applied directly to collection"
                        " types.")

    def to_ast(self):
        ast = super().to_ast()
        ast['type'] = 'collection'
        return ast


_RANGE_DEFAULT_START = 0
_RANGE_DEFAULT_END = None
_RANGE_DEFAULT_INCLUSIVE_START = True
_RANGE_DEFAULT_INCLUSIVE_END = False


class Range(Predicate):
    def __init__(self, *args, inclusive_start=_RANGE_DEFAULT_INCLUSIVE_START,
                 inclusive_end=_RANGE_DEFAULT_INCLUSIVE_END):
        # TODO: Make this not silly.
        if len(args) == 2:
            self.start, self.end = args
        elif len(args) == 1:
            self.start = _RANGE_DEFAULT_START
            self.end, = args
        elif len(args) == 0:
            self.start = _RANGE_DEFAULT_START
            self.end = _RANGE_DEFAULT_END
        else:
            raise ValueError("")
        self.inclusive_start = inclusive_start
        self.inclusive_end = inclusive_end

        super().__init__(args)

    def __contains__(self, value):
        if self.start is not None:
            if self.inclusive_start:
                if value < self.start:
                    return False
            elif value <= self.start:
                    return False

        if self.end is not None:
            if self.inclusive_end:
                if value > self.end:
                    return False
            elif value >= self.end:
                return False

        return True

    def __repr__(self):
        args = []
        if self.start is not _RANGE_DEFAULT_START:
            args.append(repr(self.start))
        if self.end is not _RANGE_DEFAULT_END:
            args.append(repr(self.end))
        if self.inclusive_start is not _RANGE_DEFAULT_INCLUSIVE_START:
            args.append('inclusive_start=%r' % self.inclusive_start)
        if self.inclusive_end is not _RANGE_DEFAULT_INCLUSIVE_END:
            args.append('inclusive_end=%r' % self.inclusive_end)

        return "%s(%s)" % (self.__class__.__name__, ', '.join(args))

    def iter_boundaries(self):
        yield from [self.start, self.end]

    def to_ast(self):
        ast = super().to_ast()
        ast['start'] = self.start
        ast['end'] = self.end
        ast['inclusive-start'] = self.inclusive_start
        ast['inclusive-end'] = self.inclusive_end
        return ast


class Choices(Predicate):
    def __init__(self, choices):
        self.choices = set(choices)

        super().__init__(choices)

    def __contains__(self, value):
        return value in self.choices

    def __repr__(self):
        return "%s({%s})" % (self.__class__.__name__,
                             repr(sorted(self.choices))[1:-1])

    def iter_boundaries(self):
        yield from self.choices

    def to_ast(self):
        ast = super().to_ast()
        ast['choices'] = list(self.choices)
        return ast


class Arguments(Predicate):
    def __init__(self, parameter):
        self.parameter = parameter

        super().__init__(parameter)

    def __contains__(self, value):
        raise NotImplementedError("Membership cannot be determined by this"
                                  " predicate directly.")

    def __repr__(self):
        return "%s(%r)" % (self.__class__.__name__, self.parameter)

    def iter_boundaries(self):
        yield from []

    def to_ast(self):
        ast = super().to_ast()
        ast['parameter'] = self.parameter
        return ast


@_symbolify(field_names=['keys', 'values'])
class Dict(_Collection):
    def _is_element_(self, value):
        if not isinstance(value, collections.abc.Mapping):
            return False
        key_type, value_type = self.fields
        for k, v in value.items():
            if k not in key_type or v not in value_type:
                return False
        return True

    def decode(self, string):
        return json.loads(string)

    def encode(self, value):
        return json.dumps(value)


@_symbolify(field_names=['elements'])
class List(_Collection):
    def _is_element_(self, value):
        if not isinstance(value, collections.abc.Sequence):
            return False
        element_type, = self.fields
        for v in value:
            if v not in element_type:
                return False
        return True

    def decode(self, string):
        return json.loads(string)

    def encode(self, value):
        return json.dumps(value)


@_symbolify(field_names=['elements'])
class Set(_Collection):
    def _is_element_(self, value):
        if not isinstance(value, collections.abc.Set):
            return False
        element_type, = self.fields
        for v in value:
            if v not in element_type:
                return False
        return True

    def decode(self, string):
        return set(json.loads(string))

    def encode(self, value):
        return json.dumps(list(value))


@_symbolify()
class Int(_Primitive):
    _valid_predicates = {Range, Arguments}

    def _is_element_(self, value):
        # Works with numpy just fine.
        return isinstance(value, numbers.Integral)

    def decode(self, string):
        return int(string)

    def encode(self, value):
        return str(value)


@_symbolify()
class Str(_Primitive):
    _valid_predicates = {Choices, Arguments}
    decode = encode = lambda self, arg: arg

    def _is_element_(self, value):
        # No reason for excluding bytes other than extreme prejudice.
        return isinstance(value, str)


@_symbolify()
class Float(_Primitive):
    _valid_predicates = {Range, Arguments}

    def _is_element_(self, value):
        # Works with numpy just fine.
        return isinstance(value, numbers.Real)

    def decode(self, string):
        return float(string)

    def encode(self, value):
        return str(value)


@_symbolify()
class Color(type(Str)):
    def _is_element_(self, value):
        # Regex from: http://stackoverflow.com/a/1636354/579416
        return bool(re.search(r'^#(?:[0-9a-fA-F]{3}){1,2}$', value))


@_symbolify()
class Metadata(_Primitive):
    _valid_predicates = set()

    def _is_element_(self, value):
        return isinstance(value, metadata.Metadata)

    def decode(self, metadata):
        # This interface should have already retrieved this object.
        if not self._is_element_(metadata):
            raise TypeError("`Metadata` must be provided by the interface"
                            " directly.")
        return metadata

    def encode(self, value):
        # TODO: Should this be the provenance representation? Does that affect
        # decode?
        return value


@_symbolify()
class MetadataCategory(_Primitive):
    _valid_predicates = set()

    def _is_element_(self, value):
        return isinstance(value, metadata.MetadataCategory)

    def decode(self, metadata_category):
        # This interface should have already retrieved this object.
        if not self._is_element_(metadata_category):
            raise TypeError("`MetadataCategory` must be provided by the"
                            " interface directly.")
        return metadata_category

    def encode(self, value):
        # TODO: Should this be the provenance representation? Does that affect
        # decode?
        return value
