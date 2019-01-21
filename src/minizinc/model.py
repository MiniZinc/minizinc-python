# For the use of self-referencing type annotations
from __future__ import annotations

import os
import tempfile
from enum import Enum
from pathlib import Path
from typing import Optional


class Method(Enum):
    SATISFY = 1
    MINIMIZE = 2
    MAXIMIZE = 3

    @classmethod
    def from_string(cls, s: str) -> Method:  # noqa
        if s == "sat":
            return cls.SATISFY
        elif s == "min":
            return cls.MINIMIZE
        elif s == "max":
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
    _method: Optional[Method]

    def __init__(self, model, data=None, driver=None):
        self._method = None
        self.files = []
        self.driver = driver
        if isinstance(model, Model):
            self.files.append(Path(model.file))
        else:
            self.files.append(Path(os.path.abspath(model)))
        if data is not None:
            self.files.append(Path(os.path.abspath(data)))

    @property
    def method(self):
        if self._method is None:
            self.driver.analyze(self)
        return self._method

    def solve(self, solver, *args, **kwargs):
        """
        Forwarding method to the driver's solve method using the instance
        :param solver: the MiniZinc solver configuration to be used
        :param args, kwargs: accepts all other arguments found in the drivers solve method
        :return: A result object containing the solution to the instance
        """
        if self.driver is not None:
            return self.driver.solve(solver, self, *args, **kwargs)
        else:
            raise LookupError("Solver is not linked to a MiniZinc driver")
