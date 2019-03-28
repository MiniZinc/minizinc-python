#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os
import platform
import shutil
from abc import ABC, abstractmethod
from ctypes import CDLL, cdll
from ctypes.util import find_library
from datetime import timedelta
from pathlib import Path
from typing import List, Optional, Type, Union

#: MiniZinc version required by the python package
required_version = (2, 2, 0)


class Driver(ABC):
    """The abstract representation of a MiniZinc driver within MiniZinc Python.

    Attributes:
        Solver (Type): A specialized Solver class to be used with the Driver
        Instance (Type): A specialized Instance class to be used with the Driver
    """
    Solver: Type
    Instance: Type

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
    def make_default(self) -> None:
        """Method to override the current default MiniZinc Python driver with the current driver.
        """
        pass

    @abstractmethod
    def __init__(self, driver: Union[Path, CDLL]):
        assert self.check_version()

    @abstractmethod
    def solve(self, solver, instance,
              timeout: Optional[timedelta] = None,
              nr_solutions: Optional[int] = None,
              processes: Optional[int] = None,
              random_seed: Optional[int] = None,
              free_search: bool = False,
              all_solutions: bool = False,
              ignore_errors=False,
              **kwargs):
        """Solves the Instance using the given solver configuration.

        Find the solutions to the given MiniZinc instance using the given solver configuration. First, the Instance will
        be ensured to be in a state where the solver specified in the solver configuration can understand the problem
        and then the solver will be requested to find the appropriate solution(s) to the problem.

        Args:
            solver (Solver): The solver configuration used to compile and solve the instance
            instance (Instance): The Instance to solve
            timeout (Optional[timedelta]): Set the time limit for the process of solving the instance.
            nr_solutions (Optional[int]): The requested number of solution. (Only available on satisfaction problems and
                when the ``-n`` flag is supported by the solver).
            processes (Optional[int]): Set the number of processes the solver can use. (Only available when the ``-p``
                flag is supported by the solver).
            random_seed (Optional[int]): Set the random seed for solver. (Only available when the ``-r`` flag is
                supported by the solver).
            free_search (bool): Allow the solver to ignore the search definition within the instance. (Only available
                when the ``-f`` flag is supported by the solver).
            all_solutions (bool): Request to solver to find all solutions. (Only available on satisfaction problems and
                when the ``-n`` flag is supported by the solver)
            ignore_errors (bool): Do not raise exceptions, when an error occurs the ``Result.status`` will be ``ERROR``.
            **kwargs: Other flags to be passed onto the solver. (TODO: NOT YET IMPLEMENTED)

        Returns:
            Result: object containing values assigned and statistical information.

        Raises:
            MiniZincError: An error occurred while compiling or solving the model instance.
        """
        pass

    @property
    @abstractmethod
    def version(self) -> str:
        """Reports the version of the MiniZinc Driver

        Report the full version of MiniZinc as reported by the driver, including the driver name, the semantic version,
        the build reference, and its authors.

        Returns:
            str: the version of as reported by the MiniZinc driver
        """
        pass

    @abstractmethod
    def check_version(self) -> bool:
        """Check if the MiniZinc version is compatible with MiniZinc Python.

        Check if the semantic version of the MiniZinc driver is compatible with the required version of the MiniZinc
        Python driver backend.

        Returns:
            bool: The compatibility of the driver.
        """
        pass


def find_driver(path: Optional[List[str]] = None, name: str = "minizinc") -> Optional[Driver]:
    """Finds MiniZinc Driver on default or specified path.

    Find driver will look for the the MiniZinc API or the MiniZinc executable to create a Driver for MiniZinc Python. If
    no path is specified, then the paths given by the environment variables appended by MiniZinc's default locations
    will be tried.

    Args:
        path: List of locations to search.
        name: Name of the API or executable.

    Returns:
        Optional[Driver]: Returns a Driver object when found or None.
    """
    if path is None:
        path_bin = os.environ.get("PATH", "").split(os.pathsep)
        path_lib = os.environ.get("LD_LIBRARY_PATH", "").split(os.pathsep)
        path_lib.extend(os.environ.get("DYLD_LIBRARY_PATH", "").split(os.pathsep))
        # Add default MiniZinc locations to the path
        if platform.system() == 'Darwin':
            MAC_LOCATIONS = [str(Path('/Applications/MiniZincIDE.app/Contents/Resources')),
                             str(Path('~/Applications/MiniZincIDE.app/Contents/Resources').expanduser())]
            path_bin.extend(MAC_LOCATIONS)
            path_lib.extend(MAC_LOCATIONS)
        elif platform.system() == 'Windows':
            WIN_LOCATIONS = [str(Path('c:/Program Files/MiniZinc')),
                             str(Path('c:/Program Files/MiniZinc IDE (bundled)')),
                             str(Path('c:/Program Files (x86)/MiniZinc')),
                             str(Path('c:/Program Files (x86)/MiniZinc IDE (bundled)'))]
            path_bin.extend(WIN_LOCATIONS)
            path_lib.extend(WIN_LOCATIONS)
    else:
        path_bin = path
        path_lib = path

    path_bin = os.pathsep.join(path_bin)
    path_lib = os.pathsep.join(path_lib)

    # Try to load the MiniZinc C API
    env_backup = os.environ.copy()
    os.environ["LD_LIBRARY_PATH"] = path_lib
    os.environ["DYLD_LIBRARY_PATH"] = path_lib
    lib = find_library(name)
    os.environ = env_backup
    if lib and Path(lib).suffix in [".dll", ".dylib", ".so"]:
        driver = cdll.LoadLibrary(lib)
    else:
        # Try to locate the MiniZinc executable
        driver = shutil.which(name, path=path_bin)
        if driver is not None:
            driver = Path(driver)

    if driver is not None:
        driver = Driver(driver)
        return driver
    return None
