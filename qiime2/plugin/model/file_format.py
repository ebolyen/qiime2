# ----------------------------------------------------------------------------
# Copyright (c) 2016-2017, QIIME 2 development team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file LICENSE, distributed with this software.
# ----------------------------------------------------------------------------

import abc

from .base import FormatBase, FormatError, ValidationError


class _FileFormat(FormatBase, metaclass=abc.ABCMeta):
    # TODO: define an abc.abstractmethod for `validate` when sniff is removed

    def _validate_(self):
        if not self.path.is_file():
            raise ValidationError("%s is not a file." % self.path)

        if hasattr(self, 'validate'):
            try:
                self.validate()
            except FormatError as e:
                raise ValidationError(
                    "%s is not a %s file: %r"
                    % (self.path, self.__class__.__name__, str(e))
                    ) from e
            except Exception as e:
                raise ValidationError("An unexpected error occured: %r"
                                      % str(e)) from e
        # TODO: remove this branch
        elif hasattr(self, 'sniff'):
            try:
                is_member = self.sniff()
            except Exception as e:
                raise ValidationError("An unexpected error occured: %r"
                                      % str(e)) from e
            if not is_member:
                raise ValidationError("%s is not a(n) %s file"
                                      % (self.path, self.__class__.__name__))
        else:
            raise NotImplementedError("%r does not implement validate."
                                      % type(self))


class TextFileFormat(_FileFormat):
    def open(self):
        mode = 'r' if self._mode == 'r' else 'r+'
        return self.path.open(mode=mode, encoding='utf8')


class BinaryFileFormat(_FileFormat):
    def open(self):
        mode = 'rb' if self._mode == 'r' else 'r+b'
        return self.path.open(mode=mode)
