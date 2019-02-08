#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at http://mozilla.org/MPL/2.0/.

import json
from abc import ABC, abstractmethod
from typing import List, Tuple

import minizinc

from .instance import Instance


class Solver(ABC):
    """The abstract representation of a MiniZinc solver configuration in MiniZinc Python.

    Attributes:
        name (str): The name of the solver.
        version (str): The version of the solver.
        id (str): A unique identifier for the solver, “reverse domain name” notation.
        executable (str): The executable for this solver that can run FlatZinc files. This can be just a file name (in
            which case the solver has to be on the current PATH), or an absolute path to the executable, or a relative
            path (which is interpreted relative to the location of the configuration file).
        mznlib (str): The solver-specific library of global constraints and redefinitions. This should be the name of a
            directory (either an absolute path or a relative path, interpreted relative to the location of the
            configuration file). For solvers whose libraries are installed in the same location as the MiniZinc standard
            library, this can also take the form -G, e.g., -Ggecode (this is mostly the case for solvers that ship with
            the MiniZinc binary distribution).
        tags (List[str]): Each solver can have one or more tags that describe its features in an abstract way. Tags can
            be used for selecting a solver using the --solver option. There is no fixed list of tags, however we
            recommend using the following tags if they match the solver’s behaviour:
            - ``cp``: for Constraint Programming solvers
            - ``mip``: for Mixed Integer Programming solvers
            - ``float``: for solvers that support float variables
            - ``api``: for solvers that use the internal C++ API
        stdFlags (List[str]): Which of the standard solver command line flags are supported by this solver. The standard
            flags are ``-a``, ``-n``, ``-s``, ``-v``, ``-p``, ``-r``, ``-f``.
        extraFlags (List[Tuple[str,str,str,str]]): Extra command line flags supported by the solver. Each entry must be
            a tuple of four strings. The first string is the name of the option (e.g. ``--special-algorithm``). The
            second string is a description that can be used to generate help output (e.g. "which special algorithm to
            use"). The third string specifies the type of the argument (``int``, ``bool``, ``float`` or ``string``). The
            fourth string is the default value.
        supportsMzn (bool): Whether the solver can run MiniZinc directly (i.e., it implements its own compilation or
            interpretation of the model).
        supportsFzn (bool): Whether the solver can run FlatZinc. This should be the case for most solvers.
        needsSolns2Out (bool): Whether the output of the solver needs to be passed through the MiniZinc output
            processor.
        needsMznExecutable (bool): Whether the solver needs to know the location of the MiniZinc executable. If true,
            it will be passed to the solver using the ``mzn-executable`` option.
        needsStdlibDir (bool): Whether the solver needs to know the location of the MiniZinc standard library directory.
            If true, it will be passed to the solver using the ``stdlib-dir`` option.
        isGUIApplication (bool): Whether the solver has its own graphical user interface, which means that MiniZinc will
            detach from the process and not wait for it to finish or to produce any output.
    """
    name: str
    version: str
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

    @abstractmethod
    def __init__(self, name: str, version: str, executable: str, driver=None):
        if driver is None:
            if minizinc.default_driver is None:
                raise LookupError("Could not initiate instance without a given or default driver")
            self.driver = minizinc.default_driver
        self.driver = driver

    @property
    @abstractmethod
    def id(self) -> str:
        pass

    def solve(self, instance: Instance, *args, **kwargs):
        """Solve supplied instance using solver.

        Solve is a forwarding method to the Driver solve method that will use the supplied instance and the current
        solver configuration.

        Args:
            solver (Solver): A MiniZinc solver configuration.
            *args: Arguments to be forwarded to the Driver solve method.
            **kwargs: Keyword arguments to be forwarded to the Driver solve method.

        Returns:
            Result: A MiniZinc Result object.
        """
        if self.driver is not None:
            return self.driver.solve(self, instance, *args, **kwargs)
        else:
            raise LookupError("Solver is not linked to a MiniZinc driver")

    def to_json(self) -> str:
        """Formulates a valid JSON specification for the Solver

        Formulates a JSON specification of the solver configuration meant to be used by MiniZinc. When stored in a
        ``.msc`` file it can be used directly as a argument to the ``--solver`` flag or stored on the MiniZinc solver
        configuration path. In the latter case it will be usable directly from the executable and visible when in
        ``minizinc --solvers``.

        Returns:
            str: JSON string containing the solver specification that can be read by MiniZinc
        """
        info = {
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
        }

        return json.dumps(info, sort_keys=True, indent=4)
