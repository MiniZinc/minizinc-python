from __future__ import annotations  # For the use of self-referencing type annotations

import json
import os
import re
import shutil
import subprocess
from abc import ABC, abstractmethod
from ctypes import cdll, CDLL
from pathlib import Path
from typing import Union

from .model import ModelInstance

#: MiniZinc version required by the python package
required_version = (2, 2, 0)

#: Default MiniZinc driver used by the python package
default_driver: Union[str, CDLL] = None


class Driver(ABC):

    @staticmethod
    @abstractmethod
    def load_solver(solver: str, minizinc: Union[Path, CDLL]) -> Driver: pass

    @abstractmethod
    def __init__(self, name: str):
        self.name = name
        assert self.minizinc_version() >= required_version

    @abstractmethod
    def solve(self, instance: ModelInstance, nr_solutions: int = None, processes: int = None, random_seed: int = None,
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

    @staticmethod
    def load_solver(solver: str, minizinc: Path) -> ExecDriver:
        # Find all available solvers
        output = subprocess.run([minizinc, "--solvers-json"], capture_output=True, check=True)
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
        driver = ExecDriver(info["name"], info["version"], info["executable"])

        # Set all specified options
        driver.mznlib = info.get("mznlib", driver.mznlib)
        driver.tags = info.get("tags", driver.mznlib)
        driver.stdFlags = info.get("stdFlags", driver.mznlib)
        driver.extraFlags = info.get("extraFlags", driver.mznlib)
        driver.supportsMzn = info.get("supportsMzn", driver.mznlib)
        driver.supportsFzn = info.get("supportsFzn", driver.mznlib)
        driver.needsSolns2Out = info.get("needsSolns2Out", driver.mznlib)
        driver.needsMznExecutable = info.get("needsMznExecutable", driver.mznlib)
        driver.needsStdlibDir = info.get("needsStdlibDir", driver.mznlib)
        driver.isGUIApplication = info.get("isGUIApplication", driver.mznlib)
        driver.id = info["id"]

        return driver

    def __init__(self, name: str, version: str, executable: str, minizinc: str = None):
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

    def solve(self, instance: ModelInstance, nr_solutions: int = None, processes: int = None, random_seed: int = None,
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
