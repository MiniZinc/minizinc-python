from __future__ import annotations  # For the use of self-referencing type annotations

import os
import tempfile
from enum import Enum
from pathlib import Path


class Method(Enum):
    SATISFY = 1
    MINIMIZE = 2
    MAXIMIZE = 3

    @classmethod
    def from_string(cls, s: str) -> Method:
        if s is "sat":
            return cls.SATISFY
        elif s is "min":
            return cls.MINIMIZE
        elif s is "max":
            return cls.MAXIMIZE
        else:
            raise ValueError("Unknown Method %r, valid options are 'sat', 'min', or 'max'" % s)


class Model:
    def __init__(self, model: str):
        self._mem = model
        self._file = None

    @property
    def file(self):
        if self._file is None:
            self._file = tempfile.NamedTemporaryFile(prefix="minizinc_model_", suffix=".mzn")
            self._file.write(self._mem.encode())
            self._file.flush()
            self._file.seek(0)
        return self._file.name

    def __del__(self):
        if self._file is not None:
            self._file.close()


class Instance:
    method: Method

    def __init__(self, model, data=None):
        self.files: list[Path] = []
        if isinstance(model, Model):
            self.files.append(Path(model.file))
        else:
            self.files.append(Path(os.path.abspath(model)))
        if data is not None:
            self.files.append(Path(os.path.abspath(data)))