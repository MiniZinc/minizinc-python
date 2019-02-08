import contextlib
import tempfile
from typing import Optional

from ..solver import Solver


class CLISolver(Solver):
    """Solver configuration usable by a CLIDriver

    Attributes:
        _id (Optional[str]): Hold the identifier of the solver configuration when its loaded directly from the driver
            and no changes have been made. When _id does not contain a value, a new id will be generated when solving
            using the solver configuration.
    """
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
        """Gives the identifier for the current solver configuration.

        Gives an identifier argument that can be used by a CLIDriver to identify the solver configuration. If the
        configuration was loaded using the driver and is thus already known, then the identifier will be yielded. If the
        configuration was changed or started from scratch, the configuration will be saved to a file and it will yield
        the name of the file.

        Yields:
            str: solver identifier to be used for the ``--solver <id>`` flag.
        """
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
