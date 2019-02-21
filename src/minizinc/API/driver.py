#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at http://mozilla.org/MPL/2.0/.

from ctypes import CDLL, c_bool, c_char_p, c_int, c_void_p
from datetime import timedelta
from typing import List, Optional, Tuple, Type

from .solver import APISolver
from .. import driver


class APIDriver(driver.Driver):
    #: Definitions of the MiniZinc API functions
    API_DEFINITIONS: List[Tuple[str, List[Type], Type]] = [
        # FUNCTION NAME, ARGUMENT TYPES, RESULT TYPE
        ("minizinc_version", [], c_char_p),
        ("minizinc_check_version", [c_int, c_int, c_int], c_bool),
        ("minizinc_error", [], c_char_p),
        ("minizinc_solver_init", [c_char_p, c_char_p, c_char_p, c_char_p], c_void_p),
        ("minizinc_solver_lookup", [c_char_p], c_void_p),
        ("minizinc_solver_load", [c_char_p], c_void_p),
        ("minizinc_solver_destroy", [c_void_p], c_bool),
    ]

    def __init__(self, library: CDLL):
        self.library = library

        for (f_name, f_args, f_res) in self.API_DEFINITIONS:
            func = getattr(self.library, f_name)
            func.argtypes = f_args
            func.restype = f_res
            setattr(self, "_" + f_name, func)

        self.Solver = type('SpecialisedAPISolver', (APISolver,), {"driver": self})
        # TODO: IMPLEMENT
        self.Instance = None

        super(APIDriver, self).__init__(library)

    def load_solver(self, tag: str):
        # TODO: IMPLEMENT
        pass

    def solve(self, solver, instance, timeout: Optional[timedelta] = None, nr_solutions: Optional[int] = None,
              processes: Optional[int] = None, random_seed: Optional[int] = None, free_search: bool = False,
              all_solutions=False, ignore_errors=False, **kwargs):
        # TODO: IMPLEMENT
        pass

    @property
    def version(self) -> str:
        return self._minizinc_version().decode()

    def check_version(self) -> bool:
        v = driver.required_version
        return self._minizinc_check_version(v[0], v[1], v[2])
