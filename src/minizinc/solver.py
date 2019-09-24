#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at http://mozilla.org/MPL/2.0/.

import contextlib
import json
import tempfile
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Set, Tuple

import minizinc

from .json import MZNJSONDecoder, MZNJSONEncoder


class Solver:
    """The representation of a MiniZinc solver configuration in MiniZinc Python.

    Attributes:
        name (str): The name of the solver.
        version (str): The version of the solver.
        id (str): A unique identifier for the solver, “reverse domain name”
            notation.
        executable (str): The executable for this solver that can run FlatZinc
            files. This can be just a file name (in which case the solver has
            to be on the current PATH), or an absolute path to the executable,
            or a relative path (which is interpreted relative to the location
            of the configuration file).
        mznlib (str): The solver-specific library of global constraints and
            redefinitions. This should be the name of a directory (either an
            absolute path or a relative path, interpreted relative to the
            location of the configuration file). For solvers whose libraries
            are installed in the same location as the MiniZinc standard
            library, this can also take the form -G, e.g., -Ggecode (this is
            mostly the case for solvers that ship with the MiniZinc binary
            distribution).
        tags (List[str]): Each solver can have one or more tags that describe
            its features in an abstract way. Tags can be used for selecting a
            solver using the --solver option. There is no fixed list of tags,
            however we recommend using the following tags if they match the
            solver’s behaviour:
            - ``cp``: for Constraint Programming solvers
            - ``mip``: for Mixed Integer Programming solvers
            - ``float``: for solvers that support float variables
            - ``api``: for solvers that use the internal C++ API
        stdFlags (List[str]): Which of the standard solver command line flags
            are supported by this solver. The standard flags are ``-a``,
            ``-n``, ``-s``, ``-v``, ``-p``, ``-r``, ``-f``.
        extraFlags (List[Tuple[str,str,str,str]]): Extra command line flags
            supported by the solver. Each entry must be a tuple of four
            strings. The first string is the name of the option (e.g.
            ``--special-algorithm``). The second string is a description that
            can be used to generate help output (e.g. "which special algorithm
            to use"). The third string specifies the type of the argument
            (``int``, ``bool``, ``float`` or ``string``). The fourth string is
            the default value.
        supportsMzn (bool): Whether the solver can run MiniZinc directly (i.e.,
            it implements its own compilation or interpretation of the model).
        supportsFzn (bool): Whether the solver can run FlatZinc. This should be
            the case for most solvers.
        needsSolns2Out (bool): Whether the output of the solver needs to be
            passed through the MiniZinc output processor.
        needsMznExecutable (bool): Whether the solver needs to know the
            location of the MiniZinc executable. If true, it will be passed to
            the solver using the ``mzn-executable`` option.
        needsStdlibDir (bool): Whether the solver needs to know the location of
            the MiniZinc standard library directory. If true, it will be passed
            to the solver using the ``stdlib-dir`` option.
        isGUIApplication (bool): Whether the solver has its own graphical user
            interface, which means that MiniZinc will detach from the process
            and not wait for it to finish or to produce any output.
        _generate (bool): True if the solver needs to be generated

    """

    name: str
    version: str
    id: str
    mznlib: str
    tags: List[str]
    stdFlags: List[str]
    extraFlags: List[Tuple[str, str, str, str]]
    executable: str
    supportsMzn: bool
    supportsFzn: bool
    needsSolns2Out: bool
    needsMznExecutable: bool
    needsStdlibDir: bool
    isGUIApplication: bool
    _generate: bool
    FIELDS = [
        "version",
        "executable",
        "mznlib",
        "tags",
        "stdFlags",
        "extraFlags",
        "supportsMzn",
        "supportsFzn",
        "needsSolns2Out",
        "needsMznExecutable",
        "needsStdlibDir",
        "isGUIApplication",
    ]

    def __init__(self, name: str, version: str, id: str, executable: str):
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

    @classmethod
    def lookup(cls, tag: str, driver=None):
        """Lookup a solver configuration in the driver registry.

        Access the MiniZinc driver's known solver configuration and find the
        configuation matching the given tag. Tags are matched in similar to
        ``minizinc --solver tag``. The order of solver configuration attributes
        that are considered is: full id, id ending, tags.

        Args:
            tag (str): tag (or id) of a solver configuration to look up.
            driver (Driver): driver which registry will be searched for the
                solver. If set to None, then ``default_driver`` will be used.

        Returns:
            Solver: MiniZinc solver configuration compatible with the driver.

        Raises:
            LookupError: No configuration could be located with the given tag.

        """
        if driver is None:
            driver = minizinc.default_driver
        from .CLI.driver import CLIDriver

        assert isinstance(driver, CLIDriver)
        if driver is not None:
            output = driver.run(["--solvers-json"])
        else:
            raise LookupError("Solver is not linked to a MiniZinc driver")
        # Find all available solvers
        solvers = json.loads(
            output.stdout
        )  # TODO: Possibly integrate with the MZNJSONDecoder

        # Find the specified solver
        lookup: Optional[Dict[str, Any]] = None
        names: Set[str] = set()
        for s in solvers:
            s_names = [s["id"], s["id"].split(".")[-1]]
            s_names.extend(s.get("tags", []))
            names = names.union(set(s_names))
            if tag in s_names:
                lookup = s
                break
        if lookup is None:
            raise LookupError(
                f"No solver id or tag '{tag}' found, available options: "
                f"{sorted([x for x in names])}"
            )

        ret = cls._from_dict(lookup)
        ret._generate = False
        return ret

    @classmethod
    def load(cls, path: Path):
        """Loads a solver configuration from a file.

        Load solver configuration from a MiniZinc solver configuration given by
        the file on the given location.

        Args:
            path (str): location to the solver configuration file to be loaded.
            driver (Driver): driver used to load the solver configuration. If
                set to None, then ``default_driver`` will be used.

        Returns:
            Solver: MiniZinc solver configuration compatible with the driver.

        Raises:
            FileNotFoundError: Solver configuration file not found.
            ValueError: File contains an invalid solver configuration.

        """
        if not path.exists():
            raise FileNotFoundError
        solver = json.loads(path.read_bytes(), cls=MZNJSONDecoder)
        if not isinstance(solver, cls):
            solver = cls._from_dict(solver)
        return solver

    @classmethod
    def _from_dict(cls, sol: Dict[str, Any]):
        if (
            sol.get("id", None) is None
            or sol.get("name", None) is None
            or sol.get("version", None) is None
        ):
            raise ValueError("Invalid solver configuration")
        # Initialize Solver
        ret = cls(sol["name"], sol["version"], sol["id"], sol.get("executable", ""))

        # Set all specified options
        ret.mznlib = sol.get("mznlib", ret.mznlib)
        ret.tags = sol.get("tags", ret.tags)
        ret.stdFlags = sol.get("stdFlags", ret.stdFlags)
        ret.extraFlags = sol.get("extraFlags", ret.extraFlags)
        ret.supportsMzn = sol.get("supportsMzn", ret.supportsMzn)
        ret.supportsFzn = sol.get("supportsFzn", ret.supportsFzn)
        ret.needsSolns2Out = sol.get("needsSolns2Out", ret.needsSolns2Out)
        ret.needsMznExecutable = sol.get("needsMznExecutable", ret.needsMznExecutable)
        ret.needsStdlibDir = sol.get("needsStdlibDir", ret.needsStdlibDir)
        ret.isGUIApplication = sol.get("isGUIApplication", ret.isGUIApplication)

        return ret

    @contextlib.contextmanager
    def configuration(self) -> Iterator[str]:
        """Gives the identifier for the current solver configuration.

        Gives an identifier argument that can be used by a CLIDriver to
        identify the solver configuration. If the configuration was loaded
        using the driver and is thus already known, then the identifier will be
        yielded. If the configuration was changed or started from scratch, the
        configuration will be saved to a file and it will yield the name of the
        file.

        Yields:
            str: solver identifier to be used for the ``--solver <id>`` flag.

        """
        if self.version == "<unknown version>":
            configuration = self.id
        else:
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

    def output_configuration(self) -> str:
        """Formulates a valid JSON specification for the Solver

        Formulates a JSON specification of the solver configuration meant to be
        used by MiniZinc. When stored in a ``.msc`` file it can be used
        directly as a argument to the ``--solver`` flag or stored on the
        MiniZinc solver configuration path. In the latter case it will be
        usable directly from the executable and visible when in ``minizinc
        --solvers``.

        Returns:
            str: JSON string containing the solver specification that can be
                read by MiniZinc

        """
        return json.dumps(self, sort_keys=True, indent=4, cls=MZNJSONEncoder)

    def __setattr__(self, key, value):
        if (
            key
            in [
                "version",
                "executable",
                "mznlib",
                "tags",
                "stdFlags",
                "extraFlags",
                "supportsMzn",
                "supportsFzn",
                "needsSolns2Out",
                "needsMznExecutable",
                "needsStdlibDir",
                "isGUIApplication",
            ]
            and getattr(self, key, None) is not value
        ):
            self._generate = True
        return super().__setattr__(key, value)
