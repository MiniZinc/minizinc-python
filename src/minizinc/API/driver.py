from ctypes import CDLL
from datetime import timedelta
from typing import Optional

from ..driver import Driver


class APIDriver(Driver):
    def __init__(self, library: CDLL):
        self.library = library

        super(APIDriver, self).__init__(library)

    def load_solver(self, tag: str):
        # TODO: IMPLEMENT
        pass

    def solve(self, solver, instance, timeout: Optional[timedelta] = None, nr_solutions: Optional[int] = None,
              processes: Optional[int] = None, random_seed: Optional[int] = None, free_search: bool = False,
              all_solutions=False, ignore_errors=False, **kwargs):
        # TODO: IMPLEMENT
        pass

    def version(self) -> str:
        # TODO: IMPLEMENT
        pass

    def check_version(self) -> bool:
        # TODO: IMPLEMENT
        pass
