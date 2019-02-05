import os
import platform
import shutil
from abc import ABC, abstractmethod
from ctypes import CDLL, cdll
from datetime import timedelta
from pathlib import Path
from typing import Any, List, Optional, Union

import minizinc

#: MiniZinc version required by the python package
required_version = (2, 2, 0)


class Driver(ABC):
    Solver: Any
    Instance: Any

    def __new__(cls, driver: Union[Path, CDLL], *args, **kwargs):
        if isinstance(driver, CDLL):
            from minizinc.API.driver import APIDriver
            cls = APIDriver
        else:
            from minizinc.CLI import CLIDriver
            cls = CLIDriver
        ret = super().__new__(cls, *args, **kwargs)
        ret.__init__(driver, *args, **kwargs)
        return ret

    @abstractmethod
    def __init__(self, driver: Union[Path, CDLL]):
        assert self.check_version()

    @abstractmethod
    def load_solver(self, tag: str):
        """
        Load a solver configuration from MiniZinc
        :param tag: the id, name, or tag of the solver to load
        :return: MiniZinc solver configuration
        """
        pass

    @abstractmethod
    def solve(self, solver, instance,
              timeout: Optional[timedelta] = None,
              nr_solutions: Optional[int] = None,
              processes: Optional[int] = None,
              random_seed: Optional[int] = None,
              free_search: bool = False,
              all_solutions=False,
              ignore_errors=False,
              **kwargs):
        pass

    @abstractmethod
    def version(self) -> str:
        """
        Version provides information about the version of the MiniZinc driver in use
        :return: a string containing the version of the MiniZinc driver
        """
        pass

    @abstractmethod
    def check_version(self) -> bool:
        """
        Check if the version of the MiniZinc driver is compatible with the Minimal version required by MiniZinc Python
        :return: result of compatibility check
        """
        pass


def find_driver(path: Optional[List[str]] = None, name: str = "minizinc", set_default=False) -> Optional[Driver]:
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
        driver = Driver(driver)
        if set_default:
            minizinc.default_driver = driver
            minizinc.Solver = driver.Solver
            minizinc.load_solver = driver.load_solver
            minizinc.Instance = driver.Instance
        return driver
    return None
