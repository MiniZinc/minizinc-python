#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at http://mozilla.org/MPL/2.0/.

import contextlib
import json
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional

import minizinc

from ..solver import Solver
from .driver import CLIDriver


class CLISolver(Solver):
    """Solver configuration usable by a CLIDriver

    Attributes:
        _generate (bool): True if the solver needs to be generated
    """
    _generate: bool

    def __init__(self, name: str, version: str, id: str, executable: str, driver: Optional[CLIDriver] = None):
        super().__init__(name, version, id, executable, driver)
        from minizinc.CLI import CLIDriver
        assert isinstance(self.driver, CLIDriver)

        # Set required fields
        self.name = name
        self.id = id
        self.version = version
        self.executable = executable
        self._generate = False

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

    @classmethod
    def lookup(cls, solver: str, driver: Optional[CLIDriver] = None):
        if driver is None:
            driver = minizinc.default_driver
        assert isinstance(driver, CLIDriver)
        if driver is not None:
            output = subprocess.run([driver.executable, "--solvers-json"], stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE, check=True)
        else:
            raise LookupError("Solver is not linked to a MiniZinc driver")
        # Find all available solvers
        solvers = json.loads(output.stdout)

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

        return cls._from_dict(lookup)

    @classmethod
    def load(cls, path: Path):
        if not path.exists():
            raise FileNotFoundError
        info = json.loads(path.read_bytes())

        solver = cls._from_dict(info)
        solver._generate = True

        return solver

    @classmethod
    def _from_dict(cls, dict: Dict[str, Any]):
        if dict.get("id", None) is None or dict.get("name", None) is None or dict.get("version", None) is None:
            raise ValueError("Invalid solver configuration")
        # Initialize Solver
        ret = cls(dict["name"], dict["version"], dict["id"], dict.get("executable", ""))

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
        if self._generate is True:
            file = tempfile.NamedTemporaryFile(prefix="minizinc_solver_", suffix=".msc")
            file.write(self.to_json().encode())
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
