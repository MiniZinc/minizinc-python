#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at http://mozilla.org/MPL/2.0/.
from ctypes import c_void_p
from pathlib import Path

from ..solver import Solver


class APISolver(Solver):
    _ptr: c_void_p

    def __init__(self, name: str, version: str, id: str, executable: str):
        pass

    def __del__(self):
        if self._ptr is not None:
            succes = self.driver._minizinc_solver_destroy(self._ptr)
            if not succes:
                msg = self.driver._minizinc_error()
                raise SystemError(msg)

    @classmethod
    def lookup(cls, tag: str):
        solver_ptr = cls.driver._minizinc_solver_lookup(tag.encode())
        if solver_ptr is None:
            msg = cls.driver._minizinc_error()
            raise LookupError(msg)
        solver = cls.__new__(cls)
        solver._ptr = solver_ptr
        return solver

    @classmethod
    def load(cls, path: Path):
        pass
