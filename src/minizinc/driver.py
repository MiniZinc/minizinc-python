#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os
import platform
import shutil
from abc import ABC, abstractmethod
from ctypes.util import find_library
from pathlib import Path
from typing import List, Optional, Type

from minizinc.instance import Instance

#: MiniZinc version required by the python package
required_version = (2, 3, 2)


class Driver(ABC):
    """The abstract representation of a MiniZinc driver within MiniZinc Python."""

    Solver: Type
    Instance: Instance

    @abstractmethod
    def make_default(self) -> None:
        """Method to override the current default MiniZinc Python driver with the
        current driver.
        """
        pass

    @abstractmethod
    def __init__(self):
        """Creates a new MiniZinc driver

        Raises:
            ConfigurationError: If an the driver version is found to be
                incompatible with MiniZinc Python
        """
        self.check_version()

    @property
    @abstractmethod
    def minizinc_version(self) -> str:
        """Reports the version of the MiniZinc Driver

        Report the full version of MiniZinc as reported by the driver,
        including the driver name, the semantic version, the build reference,
        and its authors.

        Returns:
            str: the version of as reported by the MiniZinc driver

        """
        pass

    @abstractmethod
    def check_version(self) -> None:
        """Raises an error if the MiniZinc version is incompatible with
        MiniZinc Python.

        Raises:
            ConfigurationError: An error noting the discrepancy between the
                required version of MiniZinc and the version of MiniZinc found.
        """
        pass


def find_driver(
    path: Optional[List[str]] = None, name: str = "minizinc"
) -> Optional[Driver]:
    """Finds MiniZinc Driver on default or specified path.

    Find driver will look for the the MiniZinc API or the MiniZinc executable
    to create a Driver for MiniZinc Python. If no path is specified, then the
    paths given by the environment variables appended by MiniZinc's default
    locations will be tried.

    Args:
        path: List of locations to search.
        name: Name of the API or executable.

    Returns:
        Optional[Driver]: Returns a Driver object when found or None.

    """
    driver: Optional[Driver] = None
    if path is None:
        path_bin = os.environ.get("PATH", "").split(os.pathsep)
        path_lib = os.environ.get("LD_LIBRARY_PATH", "").split(os.pathsep)
        path_lib.extend(os.environ.get("DYLD_LIBRARY_PATH", "").split(os.pathsep))
        # Add default MiniZinc locations to the path
        if platform.system() == "Darwin":
            MAC_LOCATIONS = [
                str(Path("/Applications/MiniZincIDE.app/Contents/Resources")),
                str(
                    Path(
                        "~/Applications/MiniZincIDE.app/Contents/Resources"
                    ).expanduser()
                ),
            ]
            path_bin.extend(MAC_LOCATIONS)
            path_lib.extend(MAC_LOCATIONS)
        elif platform.system() == "Windows":
            WIN_LOCATIONS = [
                str(Path("c:/Program Files/MiniZinc")),
                str(Path("c:/Program Files/MiniZinc IDE (bundled)")),
                str(Path("c:/Program Files (x86)/MiniZinc")),
                str(Path("c:/Program Files (x86)/MiniZinc IDE (bundled)")),
            ]
            path_bin.extend(WIN_LOCATIONS)
            path_lib.extend(WIN_LOCATIONS)
    else:
        path_bin = path
        path_lib = path

    path_bin_list = os.pathsep.join(path_bin)
    path_lib_list = os.pathsep.join(path_lib)

    # Try to load the MiniZinc C API
    env_backup = os.environ.copy()
    os.environ["LD_LIBRARY_PATH"] = path_lib_list
    os.environ["DYLD_LIBRARY_PATH"] = path_lib_list
    lib = find_library(name)
    os.environ.clear()
    os.environ.update(env_backup)
    if lib and Path(lib).suffix in [".dll", ".dylib", ".so"]:
        pass
        # TODO:
        # from minizinc.API import APIDriver

        # library = cdll.LoadLibrary(lib)
        # driver = APIDriver(library)
    else:
        # Try to locate the MiniZinc executable
        executable = shutil.which(name, path=path_bin_list)
        if executable is not None:
            from minizinc.CLI import CLIDriver

            driver = CLIDriver(Path(executable))

    return driver
