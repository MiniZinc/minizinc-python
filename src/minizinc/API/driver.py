#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at http://mozilla.org/MPL/2.0/.

from minizinc.driver import Driver


class APIDriver(Driver):
    pass
    #: Definitions of the MiniZinc API functions

    # API_DEFINITIONS: List[Tuple[str, List[Type], Type]] = [
    #     # FUNCTION NAME, ARGUMENT TYPES, RESULT TYPE
    #     ("minizinc_version", [], c_char_p),
    #     ("minizinc_check_version", [c_int, c_int, c_int], c_bool),
    #     ("minizinc_error", [], c_char_p),
    #     ("minizinc_solver_init", [c_char_p, c_char_p, c_char_p, c_char_p], c_void_p),
    #     ("minizinc_solver_lookup", [c_char_p], c_void_p),
    #     ("minizinc_solver_load", [c_char_p], c_void_p),
    #     ("minizinc_solver_destroy", [c_void_p], c_bool),
    #     ("minizinc_instance_init", [], c_void_p),
    #     ("minizinc_instance_destroy", [c_void_p], c_bool),
    # ]

    # def __init__(self, library: CDLL):
    #     self.library = library

    #     for (f_name, f_args, f_res) in self.API_DEFINITIONS:
    #         func = getattr(self.library, f_name)
    #         func.argtypes = f_args
    #         func.restype = f_res
    #         setattr(self, "_" + f_name, func)

    #     super(APIDriver, self).__init__(library)

    # def make_default(self) -> None:
    #     from . import APInstance, APISolver

    #     minizinc.default_driver = self
    #     minizinc.Instance = APInstance
    #     minizinc.Solver = APISolver

    # def solve(
    #     self,
    #     solver,
    #     instance,
    #     timeout: Optional[timedelta] = None,
    #     nr_solutions: Optional[int] = None,
    #     processes: Optional[int] = None,
    #     random_seed: Optional[int] = None,
    #     free_search: bool = False,
    #     all_solutions=False,
    #     ignore_errors=False,
    #     **kwargs,
    # ):
    #     # TODO: IMPLEMENT
    #     pass

    # @property
    # def minizinc_version(self) -> str:
    #     return self._minizinc_version().decode()

    # def check_version(self) -> bool:
    #     v = driver.required_version
    #     return self._minizinc_check_version(v[0], v[1], v[2])
