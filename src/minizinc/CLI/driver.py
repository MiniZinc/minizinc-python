#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at http://mozilla.org/MPL/2.0/.

import asyncio
import re
import subprocess
import warnings
from datetime import timedelta
from pathlib import Path
from typing import List, Optional, Type

import minizinc

from ..driver import Driver
from ..error import parse_error
from ..solver import Solver


def to_python_type(mzn_type: dict) -> Type:
    """Converts MiniZinc JSON type to Type

    Converts a MiniZinc JSON type definition generated by the MiniZinc CLI to a
    Python Type object. This can be used on types that result from calling
    ``minizinc --model-interface-only``.

    Args:
        mzn_type (dict): MiniZinc type definition as resulting from JSON

    Returns:
        Type: Type definition in Python

    """
    basetype = mzn_type["type"]
    if basetype == "bool":
        pytype = bool
    elif basetype == "float":
        pytype = float
    elif basetype == "int":
        pytype = int
    else:
        warnings.warn(
            "Unable to determine basetype `" + basetype + "` assuming integer type",
            FutureWarning,
        )
        pytype = int

    dim = mzn_type.get("dim", 0)
    while dim >= 1:
        pytype = List[pytype]
        dim -= 1
    return pytype


class CLIDriver(Driver):
    """Driver that interfaces with MiniZinc through the command line interface.

    The command line driver will interact with MiniZinc and its solvers through
    the use of a ``minizinc`` executable. Driving MiniZinc using its executable
    is non-incremental and can often trigger full recompilation and might
    restart the solver from the beginning when changes are made to the instance.

    Attributes:
        executable (Path): The path to the executable used to access the MiniZinc Driver

    """

    _executable: Path

    def __init__(self, executable: Path):
        self._executable = executable
        assert self._executable.exists()

        super(CLIDriver, self).__init__()

    def make_default(self) -> None:
        from . import CLIInstance

        minizinc.default_driver = self
        minizinc.Instance = CLIInstance

    def run(
        self,
        args: List[str],
        solver: Optional[Solver] = None,
        timeout: Optional[timedelta] = None,
    ):
        # TODO: Add documentation
        if timeout is not None:
            timeout = timeout.total_seconds()
        if solver is None:
            output = subprocess.run(
                [str(self._executable), "--allow-multiple-assignments"]
                + [str(arg) for arg in args],
                stdin=None,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=timeout,
            )
        else:
            with solver.configuration() as conf:
                output = subprocess.run(
                    [
                        str(self._executable),
                        "--solver",
                        conf,
                        "--allow-multiple-assignments",
                    ]
                    + [str(arg) for arg in args],
                    stdin=None,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=timeout,
                )
        if output.returncode != 0:
            raise parse_error(output.stderr)
        return output

    async def create_process(self, args: List[str], solver: Optional[Solver] = None):
        # TODO: Add documentation
        if solver is None:
            proc = await asyncio.create_subprocess_exec(
                str(self._executable),
                "--allow-multiple-assignments",
                *[str(arg) for arg in args],
                stdin=None,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
        else:
            with solver.configuration() as conf:
                proc = await asyncio.create_subprocess_exec(
                    str(self._executable),
                    "--solver",
                    conf,
                    "--allow-multiple-assignments",
                    *[str(arg) for arg in args],
                    stdin=None,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
        return proc

    @property
    def minizinc_version(self) -> tuple:
        return self.run(["--version"]).stdout.decode()

    def check_version(self):
        output = self.run(["--version"])
        match = re.search(rb"version (\d+)\.(\d+)\.(\d+)", output.stdout)
        return (
            tuple([int(i) for i in match.groups()]) >= minizinc.driver.required_version
        )
