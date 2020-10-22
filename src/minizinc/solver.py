#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at http://mozilla.org/MPL/2.0/.

import contextlib
import json
import os
import tempfile
from dataclasses import dataclass, field, fields
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Set, Tuple

import minizinc


@dataclass
class Solver:
    """The representation of a MiniZinc solver configuration in MiniZinc Python.

    Attributes:
        name (str): The name of the solver.
        version (str): The version of the solver.
        id (str): A unique identifier for the solver, “reverse domain name”
            notation.
        executable (Optional[str]): The executable for this solver that can run
            FlatZinc files. This can be just a file name (in which case the
            solver has to be on the current ``$PATH``), or an absolute path to
            the executable, or a relative path (which is interpreted relative
            to the location of the configuration file). This attribute is set
            to ``None`` if the solver is integrated into MiniZinc.
        mznlib (str): The solver-specific library of global constraints and
            redefinitions. This should be the name of a directory (either an
            absolute path or a relative path, interpreted relative to the
            location of the configuration file). For solvers whose libraries
            are installed in the same location as the MiniZinc standard
            library, this can also take the form -G, e.g., -Ggecode (this is
            mostly the case for solvers that ship with the MiniZinc binary
            distribution).
        mznlibVersion (int): *Currently undocumented in the MiniZinc
            documentation.*
        description (str):  *Currently undocumented in the MiniZinc
            documentation.*
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
        requiredFlags (List[str]):  *Currently undocumented in the MiniZinc
            documentation.*
        supportsMzn (bool): Whether the solver can run MiniZinc directly (i.e.,
            it implements its own compilation or interpretation of the model).
        supportsFzn (bool): Whether the solver can run FlatZinc. This should be
            the case for most solvers.
        supportsNL (bool): Whether the solver conforms to the AMPL NL standard.
            The NL format is used if ``supportsFZN`` is ``False``.
        needsSolns2Out (bool): Whether the output of the solver needs to be
            passed through the MiniZinc output processor.
        needsMznExecutable (bool): Whether the solver needs to know the
            location of the MiniZinc executable. If true, it will be passed to
            the solver using the ``mzn-executable`` option.
        needsStdlibDir (bool): Whether the solver needs to know the location of
            the MiniZinc standard library directory. If true, it will be passed
            to the solver using the ``stdlib-dir`` option.
        needsPathsFile (bool):  *Currently undocumented in the MiniZinc
            documentation.*
        isGUIApplication (bool): Whether the solver has its own graphical user
            interface, which means that MiniZinc will detach from the process
            and not wait for it to finish or to produce any output.
        _identifier (Optional[str]): A string to specify the solver to MiniZinc
            driver. If set to None, then a solver configuration file should be
            generated.
    """

    name: str
    version: str
    id: str
    executable: Optional[str] = None
    mznlib: str = ""
    mznlibVersion: int = 1
    description: str = ""
    tags: List[str] = field(default_factory=list)
    stdFlags: List[str] = field(default_factory=list)
    extraFlags: List[Tuple[str, str, str, str]] = field(default_factory=list)
    requiredFlags: List[str] = field(default_factory=list)
    supportsMzn: bool = False
    supportsFzn: bool = True
    supportsNL: bool = False
    needsSolns2Out: bool = False
    needsMznExecutable: bool = False
    needsStdlibDir: bool = False
    needsPathsFile: bool = False
    isGUIApplication: bool = False
    _identifier: Optional[str] = None

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
        solvers = json.loads(output.stdout)

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

        allowed_fields = set([f.name for f in fields(cls)])
        ret = cls(
            **{key: value for (key, value) in lookup.items() if key in allowed_fields}
        )
        if ret.version == "<unknown version>":
            ret._identifier = ret.id
        else:
            ret._identifier = ret.id + "@" + ret.version
        return ret

    @classmethod
    def load(cls, path: Path):
        """Loads a solver configuration from a file.

        Load solver configuration from a MiniZinc solver configuration given by
        the file on the given location.

        Args:
            path (str): location to the solver configuration file to be loaded.

        Returns:
            Solver: MiniZinc solver configuration compatible with the driver.

        Raises:
            FileNotFoundError: Solver configuration file not found.
            ValueError: File contains an invalid solver configuration.
        """
        if not path.exists():
            raise FileNotFoundError
        solver = json.loads(path.read_bytes())
        # Resolve relative paths
        for key in ["executable", "mznlib"]:
            if key in solver:
                p = Path(solver[key])
                if not p.is_absolute():
                    p = path.parent / p
                    if p.exists():
                        solver[key] = str(p.resolve())

        solver = cls(**solver)
        solver._identifier = str(path.resolve())
        return solver

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
        try:
            file = None
            if self._identifier is not None:
                yield self._identifier
            else:
                file = tempfile.NamedTemporaryFile(
                    prefix="minizinc_solver_", suffix=".msc", delete=False
                )
                file.write(self.output_configuration().encode())
                file.close()
                yield file.name
        finally:
            if file is not None:
                os.remove(file.name)

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
        return json.dumps(
            {
                "name": self.name,
                "version": self.version,
                "id": self.id,
                "executable": self.executable,
                "mznlib": self.mznlib,
                "tags": self.tags,
                "stdFlags": self.stdFlags,
                "extraFlags": self.extraFlags,
                "supportsMzn": self.supportsMzn,
                "supportsFzn": self.supportsFzn,
                "needsSolns2Out": self.needsSolns2Out,
                "needsMznExecutable": self.needsMznExecutable,
                "needsStdlibDir": self.needsStdlibDir,
                "isGUIApplication": self.isGUIApplication,
            },
            sort_keys=True,
            indent=4,
        )

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
            self._identifier = None
        return super().__setattr__(key, value)
