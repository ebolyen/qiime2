# ----------------------------------------------------------------------------
# Copyright (c) 2016-2017, QIIME 2 development team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file LICENSE, distributed with this software.
# ----------------------------------------------------------------------------
import collections
from qiime2 import Metadata
import pandas as pd

from .format import (
    FourIntsDirectoryFormat,
    MappingDirectoryFormat,
    IntSequenceFormat,
    SingleIntFormat,
    MappingFormat,
)
from .plugin import dummy_plugin


@dummy_plugin.register_transformer
def _2(data: int) -> SingleIntFormat:
    ff = SingleIntFormat()
    with ff.open() as fh:
        fh.write('%d\n' % data)
    return ff


@dummy_plugin.register_transformer
def _5(ff: SingleIntFormat) -> int:
    with ff.open() as fh:
        return int(fh.read())


@dummy_plugin.register_transformer
def _7(data: list) -> IntSequenceFormat:
    ff = IntSequenceFormat()
    with ff.open() as fh:
        for int_ in data:
            fh.write('%d\n' % int_)
    return ff


@dummy_plugin.register_transformer
def _9(ff: IntSequenceFormat) -> list:
    with ff.open() as fh:
        return list(map(int, fh.readlines()))


@dummy_plugin.register_transformer
def _10(ff: IntSequenceFormat) -> collections.Counter:
    with ff.open() as fh:
        return collections.Counter(map(int, fh.readlines()))


@dummy_plugin.register_transformer
def _11(data: dict) -> MappingDirectoryFormat:
    df = MappingDirectoryFormat()
    df.mapping.write_data(data, dict)
    return df


@dummy_plugin.register_transformer
def _12(data: dict) -> MappingFormat:
    ff = MappingFormat()
    with ff.open() as fh:
        for key, value in data.items():
            fh.write('%s\t%s\n' % (key, value))
    return ff


@dummy_plugin.register_transformer
def _13(df: MappingDirectoryFormat) -> dict:
    # If this had been a `SingleFileDirectoryFormat` then this entire
    # transformer would have been redundant (the framework could infer it).
    return df.mapping.view(dict)


@dummy_plugin.register_transformer
def _14(ff: MappingFormat) -> dict:
    data = {}
    with ff.open() as fh:
        for line in fh:
            key, value = line.rstrip('\n').split('\t')
            if key in data:
                raise ValueError(
                    "mapping.txt file must have unique keys. Key %r was "
                    "observed more than once." % key)
            data[key] = value
    return data


@dummy_plugin.register_transformer
def _134(df: MappingDirectoryFormat) -> Metadata:
    d = df.mapping.view(dict)
    return Metadata(pd.DataFrame(d, index=[0]))


@dummy_plugin.register_transformer
def _3(df: FourIntsDirectoryFormat) -> list:
    # Note: most uses of `iter_views` will need to look at the first element
    # of the series of tuples provided by iter_views
    return [x for _, x in df.single_ints.iter_views(int)]


@dummy_plugin.register_transformer
def _1(data: list) -> FourIntsDirectoryFormat:
    df = FourIntsDirectoryFormat()
    for i, int_ in enumerate(data, 1):
        df.single_ints.write_data(int_, int, num=i)
    return df
