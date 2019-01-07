from __future__ import annotations  # For the use of self-referencing type annotations

import json
import os
import re
import shutil
import subprocess
from abc import ABC, abstractmethod
from ctypes import cdll, CDLL
from pathlib import Path
from typing import Union, Optional

import minizinc
from .model import Instance, Method
from .result import Result

#: MiniZinc version required by the python package
required_version = (2, 2, 0)

#: Default MiniZinc driver used by the python package
default_driver: Optional[Driver] = None


class Driver(ABC):

    @staticmethod
    def load(driver: Union[Path, CDLL]) -> Driver:
        if isinstance(driver, CDLL):
            return LibDriver(driver)
        elif driver is not None:
            return ExecDriver(driver)
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
        assert self.minizinc_version() >= required_version

    @abstractmethod
    def solve(self, solver: minizinc.Solver, instance: Instance, nr_solutions: int = None, processes: int = None,
              random_seed: int = None, free_search: bool = False, **kwargs):
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
    # Executable path for MiniZinc
    executable: Path

    def __init__(self, executable: Path):
        self.executable = executable

        super(ExecDriver, self).__init__(executable)

    def load_solver(self, solver: str) -> minizinc.Solver:
        # Find all available solvers
        output = subprocess.run([self.executable, "--solvers-json"], capture_output=True, check=True)
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
        ret = minizinc.Solver(info["name"], info["version"], info["executable"], self)

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
        ret._id = info["id"]

        return ret

    def analyze(self, instance: Instance):
        output = subprocess.run([self.executable, "--model-interface-only"] + instance.files, capture_output=True,
                                check=True)  # TODO: Fix which files to add
        interface = json.loads(output.stdout)
        instance.method = Method.from_string(interface["method"])
        instance.input = interface["input"]  # TODO: Make python specification
        instance.output = interface["output"]  # TODO: Make python specification

    def solve(self, solver: minizinc.Solver, instance: Instance, nr_solutions: int = None, processes: int = None,
              random_seed: int = None, free_search: bool = False, **kwargs):
        self.analyze(instance)
        with solver.configuration() as conf:
            # Set standard command line arguments
            cmd = [self.executable, "--solver", conf, "--output-mode", "json", "--output-time"]
            # Enable statistics if possible
            if "-s" in solver.stdFlags:
                cmd.append("-s")

            # TODO: -n / -a flag
            # Set number of processes to be used
            if processes is not None:
                if "-p" not in solver.stdFlags:
                    raise NotImplementedError("Solver does not support the -p flag")
                cmd.extend(["-p", processes])
            # Set random seed to be used
            if random_seed is not None:
                if "-r" not in solver.stdFlags:
                    raise NotImplementedError("Solver does not support the -r flag")
                cmd.extend(["-r", random_seed])
            # Enable free search if specified
            if free_search:
                if "-f" not in solver.stdFlags:
                    raise NotImplementedError("Solver does not support the -f flag")
                cmd.append("-f")

            # Add files as last arguments
            cmd.extend(instance.files)
            # Run the MiniZinc process
            output = subprocess.run(cmd, capture_output=True, check=False)
            return Result.from_process(instance, output)

    def minizinc_version(self) -> tuple:
        output = subprocess.run([self.executable, "--version"], capture_output=True, check=True)
        match = re.search(rb"version (\d+)\.(\d+)\.(\d+)", output.stdout)
        return tuple([int(i) for i in match.groups()])


def load_solver(tag: str) -> Optional[minizinc.Solver]:
    """
    Load solver from the configuration known to MiniZinc
    :param tag: the id, name, or tag of the solver to load
    :return: A MiniZinc solver configuration if it is known
    """
    if default_driver is not None:
        return default_driver.load_solver(tag)
    else:
        raise FileExistsError("MiniZinc driver not found")  # TODO: Fix Error


def find_minizinc(name: str = "minizinc", path: list = None) -> Optional[Driver]:
    """
    Find MiniZinc driver on default or specified path
    :param name: Name of the executable or library
    :param path: List of locations to search
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
        return Driver.load(driver)
    return None
