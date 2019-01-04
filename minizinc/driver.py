from __future__ import annotations  # For the use of self-referencing type annotations

import json
import os
import re
import shutil
import subprocess
from abc import ABC, abstractmethod
from ctypes import cdll, CDLL
from pathlib import Path
from typing import Union, List, Any, Tuple

from .model import ModelInstance

#: MiniZinc version required by the python package
required_version = (2, 2, 0)

#: Default MiniZinc driver used by the python package
default_driver: Union[str, CDLL] = None


class Driver(ABC):

    name: str

    @classmethod
    @abstractmethod
    def load_solver(cls, solver: str, driver: Union[Path, CDLL]) -> Driver:
        """
        Initialize driver using a configuration known to MiniZinc
        :param solver: the id, name, or tag of the solver to load
        :param driver: the MiniZinc base driver to use, falls back to default_driver
        :return: MiniZinc driver configured with the solver
        """
        pass

    @abstractmethod
    def __init__(self, name: str):
        self.name = name
        assert self.minizinc_version() >= required_version

    @abstractmethod
    def solve(self, instance: Instance, nr_solutions: int = None, processes: int = None, random_seed: int = None,
              free_search: bool = False, **kwargs):
        pass

    @abstractmethod
    def minizinc_version(self) -> tuple:
        """
        Returns a tuple containing the semantic version of the MiniZinc version given
        :return: tuple containing the MiniZinc version
        """
        pass


class LibDriver(Driver):
    pass


class ExecDriver(Driver):

    # Solver Configuration Options
    version: Tuple[int, int, int]
    mznlib: str
    tags: List[str]
    executable: str
    supportsMzn: bool
    supportsFzn: bool
    needsSolns2Out: bool
    needsMznExecutable: bool
    needsStdlibDir: bool
    isGUIApplication: bool

    @classmethod
    def load_solver(cls, solver: str, driver: Path) -> ExecDriver:
        # Find all available solvers
        output = subprocess.run([driver, "--solvers-json"], capture_output=True, check=True)
        solvers = json.loads(output.stdout)

        # Find the specified solver
        info = None
        names = set()
        for s in solvers:
            s_names = [s["id"], s["id"].split(".")[-1]]
            s_names.extend(s.get("tags", []))
            names = names.union(set(s_names))
            if solver in s_names:
                info = s
                break
        if info is None:
            raise LookupError(
                "No solver id or tag '%s' found, available options: %s" % (solver, sorted([x for x in names])))

        # Initialize driver
        ret = cls(info["name"], info["version"], info["executable"], driver)

        # Set all specified options
        ret.mznlib = info.get("mznlib", ret.mznlib)
        ret.tags = info.get("tags", ret.mznlib)
        ret.stdFlags = info.get("stdFlags", ret.mznlib)
        ret.extraFlags = info.get("extraFlags", ret.mznlib)
        ret.supportsMzn = info.get("supportsMzn", ret.mznlib)
        ret.supportsFzn = info.get("supportsFzn", ret.mznlib)
        ret.needsSolns2Out = info.get("needsSolns2Out", ret.mznlib)
        ret.needsMznExecutable = info.get("needsMznExecutable", ret.mznlib)
        ret.needsStdlibDir = info.get("needsStdlibDir", ret.mznlib)
        ret.isGUIApplication = info.get("isGUIApplication", ret.mznlib)
        ret.id = info["id"]

        return ret

    def __init__(self, name: str, version: str, executable: str, minizinc: Path = None):
        if minizinc is None:
            minizinc = default_driver
        self.driver = minizinc

        # Set required fields
        super().__init__(name)
        self.id = None
        match = re.search(r"(\d+)\.(\d+)\.(\d+)", version)
        self.version = tuple([int(i) for i in match.groups()])
        self.executable = executable

        # Initialise optional fields
        self.mznlib = ""
        self.tags = []
        self.stdFlags = []
        self.extraFlags = []
        self.supportsMzn = False
        self.supportsFzn = True
        self.needsSolns2Out = False
        self.needsMznExecutable = False
        self.needsStdlibDir = False
        self.isGUIApplication = False

    def solve(self, instance: Instance, nr_solutions: int = None, processes: int = None, random_seed: int = None,
              free_search: bool = False, **kwargs):
        pass

    def minizinc_version(self) -> tuple:
        output = subprocess.run([self.driver, "--version"], capture_output=True, check=True)
        match = re.search(r"version (\d+)\.(\d+)\.(\d+)", output.stdout.decode())
        return tuple([int(i) for i in match.groups()])

    def __setattr__(self, key, value):
        if key in ["version", "executable", "mznlib", "tags", "stdFlags", "extraFlags", "supportsMzn", "supportsFzn",
                   "needsSolns2Out", "needsMznExecutable", "needsStdlibDir", "isGUIApplication"] \
                and getattr(self, key, None) is not value:
            self.id = None
        return super().__setattr__(key, value)


def is_library(elem) -> bool:
    """
    Returns true if elem is an library format
    """
    return isinstance(elem, CDLL)


def load_solver(solver: str, minizinc: Union[CDLL, Path] = None) -> Driver:
    """
    Load solver from the configuration known to MiniZinc
    :param solver: the id, name, or tag of the solver to load
    :param minizinc: the MiniZinc base driver to use, falls back to default_driver
    :return: MiniZinc driver configured with the solver
    """
    if minizinc is None:
        minizinc = default_driver

    if is_library(minizinc):
        return LibDriver.load_solver(solver, minizinc)
    elif minizinc is not None:
        return ExecDriver.load_solver(solver, minizinc)
    else:
        raise FileExistsError("MiniZinc driver not found")


def find_minizinc(name: str = "minizinc", path: list = None) -> Union[CDLL, Path, None]:
    """
    Find MiniZinc driver on default or specified path
    :param name: Name of the executable or library
    :param path: List of locations to search
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

    return driver
