from __future__ import annotations  # For the use of self-referencing type annotations

import os
import platform
import shutil
from abc import ABC, abstractmethod
from ctypes import CDLL, cdll
from datetime import timedelta
from pathlib import Path
from typing import Union, Optional

# Driver should not import any classes directly
import minizinc.model
import minizinc.solver

#: MiniZinc version required by the python package
required_version = (2, 2, 0)


class Driver(ABC):

    @staticmethod
    def load(driver: Union[Path, CDLL]) -> Driver:
        if isinstance(driver, CDLL):
            from minizinc.API.driver import APIDriver
            return APIDriver(driver)
        elif driver is not None:
            from minizinc.CLI import CLIDriver
            return CLIDriver(driver)
        else:
            raise FileExistsError("MiniZinc driver not found")

    def __init__(self):
        self.Solver = self.load_solver
        self.Instance = self._create_instance
        assert self.version() >= required_version

    @abstractmethod
    def load_solver(self, tag: str) -> minizinc.solver.Solver:
        """
        Initialize driver using a configuration known to MiniZinc
        :param tag: the id, name, or tag of the solver to load
        :return: MiniZinc solver configuration
        """
        pass

    @abstractmethod
    def solve(self, solver: minizinc.solver.Solver, instance: minizinc.model.Instance,
              timeout: Optional[timedelta] = None,
              nr_solutions: Optional[int] = None,
              processes: Optional[int] = None,
              random_seed: Optional[int] = None,
              free_search: bool = False,
              all_solutions=False,
              **kwargs):
        pass

    @abstractmethod
    def version(self) -> tuple:
        """
        Returns a tuple containing the semantic version of the MiniZinc version given
        :return: tuple containing the MiniZinc version
        """
        pass

    @abstractmethod
    def _create_instance(self, model, data=None) -> minizinc.Instance:
        pass


def load_minizinc(path: Optional[list[str]] = None, name: str = "minizinc", set_default=True) -> Optional[Driver]:
    """
    Find MiniZinc driver on default or specified path
    :param path: List of locations to search
    :param name: Name of the executable or library
    :param set_default: Set driver as default if

    :return: A MiniZinc Driver object, if the driver is found
    """
    if path is None:
        path_bin = os.environ.get("PATH", "").split(os.pathsep)
        path_lib = os.environ.get("LD_LIBRARY_PATH", "").split(os.pathsep)
        # Add default MiniZinc locations to the path
        if platform.system() == 'Darwin':
            MAC_LOCATIONS = [str(Path('/Applications/MiniZincIDE.app/Contents/Resources')),
                          str(Path('~/Applications/MiniZincIDE.app/Contents/Resources').expanduser())]
            path_bin.extend(MAC_LOCATIONS)
            # TODO: LD_LIBRARY_PATH
        elif platform.system() == 'Windows':
            WIN_LOCATIONS = [str(Path('c:/Program Files/MiniZinc')),
                             str(Path('c:/Program Files/MiniZinc IDE (bundled)')),
                             str(Path('c:/Program Files (x86)/MiniZinc')),
                             str(Path('c:/Program Files (x86)/MiniZinc IDE (bundled)'))]
            path_bin.extend(WIN_LOCATIONS)
            # TODO: LD_LIBRARY_PATH
    else:
        path_bin = path
        path_lib = path

    path_bin = os.pathsep.join(path_bin)
    path_lib = os.pathsep.join(path_lib)

    try:
        # Try to load the MiniZinc C API
        env_backup = os.environ.copy()
        os.environ["LD_LIBRARY_PATH"] = path_lib
        driver = cdll.LoadLibrary(name)
        os.environ = env_backup
    except OSError:
        # Try to locate the MiniZinc executable
        driver = shutil.which(name, path=path_bin)
        if driver is not None:
            driver = Path(driver)

    if driver is not None:
        driver = Driver.load(driver)
        if set_default:
            minizinc.default_driver = driver
            minizinc.Solver = driver.Solver
            minizinc.Instance = driver.Instance
        return driver
    return None
