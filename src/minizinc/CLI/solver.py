import contextlib
import tempfile
from typing import Optional

from ..solver import Solver


class CLISolver(Solver):
    # Solver identifier for MiniZinc driver
    _id: Optional[str]

    def __init__(self, name: str, version: str, executable: str, driver=None):
        super().__init__(name, version, executable, driver)
        from minizinc.CLI import CLIDriver
        if not isinstance(self.driver, CLIDriver):
            raise TypeError(str(type(self.driver)) + " is not an instance of CLIDriver")

        # Set required fields
        self.name = name
        self._id = None
        self.version = version
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

    @property
    def id(self) -> str:
        if self._id is None:
            return "org.minizinc.python." + self.name.lower()
        else:
            return self._id

    @contextlib.contextmanager
    def configuration(self) -> str:
        file = None
        if self._id is None:
            file = tempfile.NamedTemporaryFile(prefix="minizinc_solver_", suffix=".msc")
            file.write(self.to_json().encode())
            file.flush()
            file.seek(0)
            self._id = file.name
        try:
            yield self._id
        finally:
            if file is not None:
                file.close()
                self._id = None

    def __setattr__(self, key, value):
        if key in ["version", "executable", "mznlib", "tags", "stdFlags", "extraFlags", "supportsMzn", "supportsFzn",
                   "needsSolns2Out", "needsMznExecutable", "needsStdlibDir", "isGUIApplication"] \
                and getattr(self, key, None) is not value:
            self._id = None
        return super().__setattr__(key, value)
