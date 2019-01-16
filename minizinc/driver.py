from __future__ import annotations  # For the use of self-referencing type annotations

import os
import shutil
from abc import ABC, abstractmethod
from ctypes import CDLL, cdll
from pathlib import Path
from typing import Union, Optional

# Driver should not import any classes directly
import minizinc.model

#: MiniZinc version required by the python package
required_version = (2, 2, 0)

#: Default MiniZinc driver used by the python package
default_driver: Optional[Driver] = None


class Driver(ABC):

    @staticmethod
    def load(driver: Union[Path, CDLL]) -> Driver:
        if isinstance(driver, CDLL):
            from minizinc.lib.driver import LibDriver
            return LibDriver(driver)
        elif driver is not None:
            from minizinc.bin import BinDriver
            return BinDriver(driver)
        else:
            raise FileExistsError("MiniZinc driver not found")

    @abstractmethod
    def load_solver(self, tag: str) -> minizinc.Solver:
        """
        Initialize driver using a configuration known to MiniZinc
        :param tag: the id, name, or tag of the solver to load
        :return: MiniZinc solver configuration
        """
        pass

    @abstractmethod
    def __init__(self, driver_location: Union[Path, CDLL]):
        self.Solver = self.load_solver
        self.Instance = self._create_instance
        assert self.minizinc_version() >= required_version

    @abstractmethod
    def solve(self, solver: minizinc.Solver, instance: minizinc.model.Instance,
              nr_solutions: Optional[int] = None,
              processes: Optional[int] = None,
              random_seed: Optional[int] = None,
              free_search: bool = False,
              all_solutions=False,
              **kwargs):
        pass

    @abstractmethod
    def minizinc_version(self) -> tuple:
        """
        Returns a tuple containing the semantic version of the MiniZinc version given
        :return: tuple containing the MiniZinc version
        """
        pass

    @abstractmethod
    def _create_instance(self, model, data=None) -> minizinc.Instance:
        pass


def load_minizinc(name: str = "minizinc", path: list = None, set_default=True) -> Optional[Driver]:
    """
    Find MiniZinc driver on default or specified path
    :param name: Name of the executable or library
    :param path: List of locations to search
    :param set_default: Set driver as default if

    :return: A MiniZinc Driver object, if the driver is found
    """
    try:
        # Try to load the MiniZinc C API
        if path is None:
            driver = cdll.LoadLibrary(name)
        else:
            env_backup = os.environ.copy()
            _path = os.environ["LD_LIBRARY_PATH"] = os.pathsep.join(path)
            driver = cdll.LoadLibrary(name)
            os.environ = env_backup
    except OSError:
        # Try to locate the MiniZinc executable
        driver = shutil.which(name, path=path)
        if driver:
            driver = Path(driver)

    if driver is not None:
        driver = Driver.load(driver)
        if set_default:
            minizinc.Solver = driver.Solver
            minizinc.Instance = driver.Instance
        return driver
    return None
