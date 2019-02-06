from ctypes import CDLL, c_bool, c_char_p, c_int
from datetime import timedelta
from typing import List, Optional, Tuple, Type

from .. import driver


class APIDriver(driver.Driver):
    #: Definitions of the MiniZinc API functions
    API_DEFINITIONS: List[Tuple[str, List[Type], Type]] = [
        # FUNCTION NAME, ARGUMENT TYPES, RESULT TYPE
        ("minizinc_version", [], c_char_p),
        ("minizinc_check_version", [c_int, c_int, c_int], c_bool),
    ]

    def __init__(self, library: CDLL):
        self.library = library

        for (f_name, f_args, f_res) in self.API_DEFINITIONS:
            func = getattr(self.library, f_name)
            func.argtypes = f_args
            func.restype = f_res
            setattr(self, "_" + f_name, func)

        # TODO: IMPLEMENT
        self.Solver = None
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
