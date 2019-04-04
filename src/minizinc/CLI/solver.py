#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at http://mozilla.org/MPL/2.0/.

import contextlib
import json
import subprocess
import tempfile
from datetime import timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import minizinc
from minizinc.json import MZNJSONDecoder

from ..instance import Instance
from ..model import Method
from ..result import Result
from ..solver import Solver
from .driver import CLIDriver, to_python_type


class CLISolver(Solver, CLIDriver):
    """Solver configuration usable by a CLIDriver

    Attributes:
        _generate (bool): True if the solver needs to be generated
    """
    _generate: bool
    FIELDS = ["version", "executable", "mznlib", "tags", "stdFlags", "extraFlags", "supportsMzn", "supportsFzn",
              "needsSolns2Out", "needsMznExecutable", "needsStdlibDir", "isGUIApplication"]

    def __init__(self, name: str, version: str, id: str, executable: str, driver: Optional[CLIDriver] = None):
        # Set required fields
        self.name = name
        self.id = id
        self.version = version
        self.executable = executable
        self._generate = True

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

        if driver is not None:
            CLIDriver.__init__(self, driver._executable)
        else:
            assert isinstance(minizinc.default_driver, CLIDriver)
            CLIDriver.__init__(self, minizinc.default_driver._executable)

    @classmethod
    def lookup(cls, solver: str, driver: Optional[CLIDriver] = None):
        if driver is None:
            driver = minizinc.default_driver
        assert isinstance(driver, CLIDriver)
        if driver is not None:
            output = subprocess.run([driver._executable, "--solvers-json"], stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE, check=True)
        else:
            raise LookupError("Solver is not linked to a MiniZinc driver")
        # Find all available solvers
        solvers = json.loads(output.stdout)  # TODO: Possibly integrate with the MZNJSONDecoder

        # Find the specified solver
        lookup = None
        names = set()
        for s in solvers:
            s_names = [s["id"], s["id"].split(".")[-1]]
            s_names.extend(s.get("tags", []))
            names = names.union(set(s_names))
            if solver in s_names:
                lookup = s
                break
        if lookup is None:
            raise LookupError("No solver id or tag '%s' found, available options: %s"
                              % (solver, sorted([x for x in names])))

        ret = cls._from_dict(lookup, driver)
        ret._generate = False
        return ret

    @classmethod
    def load(cls, path: Path, driver: Optional[CLIDriver] = None):
        if not path.exists():
            raise FileNotFoundError
        solver = json.loads(path.read_bytes(), cls=MZNJSONDecoder)
        if isinstance(solver, cls):
            solver = cls._from_dict(solver)
        return solver

    @classmethod
    def _from_dict(cls, dict: Dict[str, Any], driver: Optional[CLIDriver] = None):
        if dict.get("id", None) is None or dict.get("name", None) is None or dict.get("version", None) is None:
            raise ValueError("Invalid solver configuration")
        # Initialize Solver
        ret = cls(dict["name"], dict["version"], dict["id"], dict.get("executable", ""), driver)

        # Set all specified options
        ret.mznlib = dict.get("mznlib", ret.mznlib)
        ret.tags = dict.get("tags", ret.mznlib)
        ret.stdFlags = dict.get("stdFlags", ret.mznlib)
        ret.extraFlags = dict.get("extraFlags", ret.extraFlags)
        ret.supportsMzn = dict.get("supportsMzn", ret.mznlib)
        ret.supportsFzn = dict.get("supportsFzn", ret.mznlib)
        ret.needsSolns2Out = dict.get("needsSolns2Out", ret.mznlib)
        ret.needsMznExecutable = dict.get("needsMznExecutable", ret.mznlib)
        ret.needsStdlibDir = dict.get("needsStdlibDir", ret.mznlib)
        ret.isGUIApplication = dict.get("isGUIApplication", ret.mznlib)

        return ret

    def _run(self, args: List[str]):
        with self.configuration() as config:
            return super()._run(["--solver", config] + args)

    def solve(self, instance: Instance,
              timeout: Optional[timedelta] = None,
              nr_solutions: Optional[int] = None,
              processes: Optional[int] = None,
              random_seed: Optional[int] = None,
              all_solutions=False,
              free_search: bool = False,
              ignore_errors=False,
              **kwargs):
        from .instance import CLIInstance
        assert isinstance(instance, CLIInstance)
        # Set standard command line arguments
        cmd = ["--output-mode", "json", "--output-time", "--output-objective"]
        # Enable statistics if possible
        if "-s" in self.stdFlags:
            cmd.append("-s")

        # Process number of solutions to be generated
        if all_solutions:
            if nr_solutions is not None:
                raise ValueError("The number of solutions cannot be limited when looking for all solutions")
            if instance.method != Method.SATISFY:
                raise NotImplementedError("Finding all optimal solutions is not yet implemented")
            if "-a" not in self.stdFlags:
                raise NotImplementedError("Solver does not support the -a flag")
            cmd.append("-a")
        elif nr_solutions is not None:
            if nr_solutions <= 0:
                raise ValueError("The number of solutions can only be set to a positive integer number")
            if instance.method != Method.SATISFY:
                raise NotImplementedError("Finding all optimal solutions is not yet implemented")
            if "-n" not in self.stdFlags:
                raise NotImplementedError("Solver does not support the -n flag")
            cmd.extend(["-n", str(nr_solutions)])
        if "-a" in self.stdFlags and instance.method != Method.SATISFY:
            cmd.append("-a")
        # Set number of processes to be used
        if processes is not None:
            if "-p" not in self.stdFlags:
                raise NotImplementedError("Solver does not support the -p flag")
            cmd.extend(["-p", str(processes)])
        # Set random seed to be used
        if random_seed is not None:
            if "-r" not in self.stdFlags:
                raise NotImplementedError("Solver does not support the -r flag")
            cmd.extend(["-r", str(random_seed)])
        # Enable free search if specified
        if free_search:
            if "-f" not in self.stdFlags:
                raise NotImplementedError("Solver does not support the -f flag")
            cmd.append("-f")

        # Set time limit for the MiniZinc solving
        if timeout is not None:
            cmd.extend(["--time-limit", str(int(timeout.total_seconds() * 1000))])

        # Add files as last arguments
        with instance.files() as files:
            cmd.extend(files)
            # Run the MiniZinc process
            output = self._run(cmd)
        return Result.from_process(instance, output, ignore_errors)

    def analyse(self, instance: Instance):
        """Discovers basic information about a CLIInstance

        Analyses a given instance and discovers basic information about set model such as the solving method, the input
        parameters, and the output parameters. The information found will be stored among the attributes of the
        instance.

        Args:
            instance: The instance to be analysed and filled.
        """
        from . import CLIInstance
        assert isinstance(instance, CLIInstance)
        with instance.files() as files:
            output = self._run(["--model-interface-only"] + files)
        interface = json.loads(output.stdout)  # TODO: Possibly integrate with the MZNJSONDecoder
        instance._method = Method.from_string(interface["method"])
        instance.input = {}
        for key, value in interface["input"].items():
            instance.input[key] = to_python_type(value)
        instance.output = {}
        for (key, value) in interface["output"].items():
            instance.output[key] = to_python_type(value)

    @contextlib.contextmanager
    def configuration(self) -> str:
        """Gives the identifier for the current solver configuration.

        Gives an identifier argument that can be used by a CLIDriver to identify the solver configuration. If the
        configuration was loaded using the driver and is thus already known, then the identifier will be yielded. If the
        configuration was changed or started from scratch, the configuration will be saved to a file and it will yield
        the name of the file.

        Yields:
            str: solver identifier to be used for the ``--solver <id>`` flag.
        """
        configuration = self.id + "@" + self.version
        file = None
        if self._generate:
            file = tempfile.NamedTemporaryFile(prefix="minizinc_solver_", suffix=".msc")
            file.write(self.output_configuration().encode())
            file.flush()
            file.seek(0)
            configuration = file.name
        try:
            yield configuration
        finally:
            if file is not None:
                file.close()

    def __setattr__(self, key, value):
        if key in ["version", "executable", "mznlib", "tags", "stdFlags", "extraFlags", "supportsMzn", "supportsFzn",
                   "needsSolns2Out", "needsMznExecutable", "needsStdlibDir", "isGUIApplication"] \
                and getattr(self, key, None) is not value:
            self._generate = True
        return super().__setattr__(key, value)
