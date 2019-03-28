#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at http://mozilla.org/MPL/2.0/.
from ctypes import c_void_p
from pathlib import Path
from typing import Optional

import minizinc

from ..solver import Solver
from .driver import APIDriver


class APISolver(Solver):
    _ptr: c_void_p

    def __init__(self, name: str, version: str, id: str, executable: str, driver: Optional[APIDriver] = None):
        super().__init__(name, version, id, executable, driver)
        assert isinstance(self.driver, APIDriver)
        self._ptr = self.driver._minizinc_solver_init(name.encode(), version.encode(), id.encode(), executable.encode())
        if self._ptr is None:
            msg = self.driver._minizinc_error()
            raise SystemError(msg.decode())

    def __del__(self):
        if self._ptr is not None:
            succes = self.driver._minizinc_solver_destroy(self._ptr)
            if not succes:
                msg = self.driver._minizinc_error()
                raise SystemError(msg.decode())

    @classmethod
    def lookup(cls, tag: str, driver: Optional[APIDriver] = None):
        if driver is None:
            driver = minizinc.default_driver
        assert isinstance(driver, APISolver)
        solver_ptr = driver._minizinc_solver_lookup(tag.encode())
        if solver_ptr is None:
            msg = driver._minizinc_error()
            raise LookupError(msg.decode())
        solver = cls.__new__(cls)
        solver._ptr = solver_ptr
        return solver

    @classmethod
    def load(cls, path: Path):
        if not path.exists():
            raise FileNotFoundError
        solver_ptr = cls.driver._minizinc_solver_load(str(path.absolute()).encode())
        if solver_ptr is None:
            msg = cls.driver._minizinc_error()
            raise ValueError(msg.decode())
        solver = cls.__new__(cls)
        solver._ptr = solver_ptr
        return solver
