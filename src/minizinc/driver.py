#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os
import platform
import re
import shutil
import subprocess
import sys
from asyncio import create_subprocess_exec
from asyncio.subprocess import PIPE, Process
from dataclasses import fields
from json import loads
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import minizinc

from .error import ConfigurationError, parse_error
from .json import decode_json_stream
from .solver import Solver

#: MiniZinc version required by the python package
CLI_REQUIRED_VERSION = (2, 5, 0)
#: Default locations on MacOS where the MiniZinc packaged release would be installed
MAC_LOCATIONS = [
    str(Path("/Applications/MiniZincIDE.app/Contents/Resources")),
    str(Path("~/Applications/MiniZincIDE.app/Contents/Resources").expanduser()),
]
#: Default locations on Windows where the MiniZinc packaged release would be installed
WIN_LOCATIONS = [
    str(Path("c:/Program Files/MiniZinc")),
    str(Path("c:/Program Files/MiniZinc IDE (bundled)")),
    str(Path("c:/Program Files (x86)/MiniZinc")),
    str(Path("c:/Program Files (x86)/MiniZinc IDE (bundled)")),
]


class Driver:
    """Driver that interfaces with MiniZinc through the command line interface.

    The command line driver will interact with MiniZinc and its solvers through
    the use of a ``minizinc`` executable. Driving MiniZinc using its executable
    is non-incremental and can often trigger full recompilation and might
    restart the solver from the beginning when changes are made to the instance.

    Raises:
        ConfigurationError: If an the driver version is found to be incompatible with
            MiniZinc Python

    Attributes:
        _executable (Path): The path to the executable used to access the MiniZinc
    """

    _executable: Path
    _solver_cache: Optional[Dict[str, List[Solver]]] = None
    _version: Optional[Tuple[int, ...]] = None

    def __init__(self, executable: Path):
        self._executable = executable
        if not self._executable.exists():
            raise ConfigurationError(
                f"No MiniZinc executable was found at '{self._executable}'."
            )

        if self.parsed_version < CLI_REQUIRED_VERSION:
            raise ConfigurationError(
                f"The MiniZinc driver found at '{self._executable}' has "
                f"version {self.parsed_version}. The minimal required version is "
                f"{CLI_REQUIRED_VERSION}."
            )

    def make_default(self) -> None:
        """Method to override the current default MiniZinc Python driver with the
        current driver.
        """
        minizinc.default_driver = self

    @property
    def executable(self) -> Path:
        """Reports the Path of the MiniZinc executable used by the Driver object

        Returns:
            Path: location of the MiniZinc executable
        """
        return self._executable

    @property
    def minizinc_version(self) -> str:
        """Reports the version text of the MiniZinc Driver

        Report the full version text of MiniZinc as reported by the driver,
        including the driver name, the semantic version, the build reference,
        and its authors.

        Returns:
            str: the version of as reported by the MiniZinc driver
        """
        # Note: cannot use "_run" as it already required the parsed version
        return subprocess.run(
            [str(self._executable), "--version"],
            stdin=None,
            stdout=PIPE,
            stderr=PIPE,
        ).stdout.decode()

    @property
    def parsed_version(self) -> Tuple[int, ...]:
        """Reports the version of the MiniZinc Driver

        Report the parsed version of the MiniZinc Driver as a tuple of integers.
        The tuple is ordered: major, minor, patch.

        Returns:
            Tuple[int, ...]: the parsd version reported by the MiniZinc driver
        """
        if self._version is None:
            match = re.search(r"version (\d+)\.(\d+)\.(\d+)", self.minizinc_version)
            assert match
            self._version = tuple([int(i) for i in match.groups()])
        return self._version

    def available_solvers(self, refresh=False):
        """Returns a list of available solvers

        This method returns the list of solvers available to the Driver object
        according to the current environment. Note that the list of solvers might
        be cached for future usage. The refresh argument can be used to ignore
        the current cache.

        Args:
            refresh (bool): When set to true, the Driver will rediscover the
                available solvers from the current environment.

        Returns:
            Dict[str, List[Solver]]: A dictionary that maps solver tags to MiniZinc
                solver configurations that can be used with the Driver object.
        """
        if not refresh and self._solver_cache is not None:
            return self._solver_cache

        # Find all available solvers
        output = self._run(["--solvers-json"])
        solvers = loads(output.stdout)

        # Construct Solver objects
        self._solver_cache = {}
        allowed_fields = {f.name for f in fields(Solver)}
        for s in solvers:
            obj = Solver(
                **{key: value for (key, value) in s.items() if key in allowed_fields}
            )
            if obj.version == "<unknown version>":
                obj._identifier = obj.id
            else:
                obj._identifier = obj.id + "@" + obj.version

            names = s.get("tags", [])
            names.extend([s["id"], s["id"].split(".")[-1]])
            for name in names:
                self._solver_cache.setdefault(name, []).append(obj)

        return self._solver_cache

    def _run(
        self,
        args: List[Any],
        solver: Optional[Solver] = None,
    ):
        """Start a driver process with given arguments

        Args:
            args (List[str]): direct arguments to the driver
            solver (Union[str, Path, None]): Solver configuration string
                guaranteed by the user to be valid until the process has ended.
        """
        # TODO: Add documentation
        windows_spawn_options: Dict[str, Any] = {}
        if sys.platform == "win32":
            # On Windows, MiniZinc terminates its subprocesses by generating a
            # Ctrl+C event for its own console using GenerateConsoleCtrlEvent.
            # Therefore, we must spawn it in its own console to avoid receiving
            # that Ctrl+C ourselves.
            #
            # On POSIX systems, MiniZinc terminates its subprocesses by sending
            # SIGTERM to the solver's process group, so this workaround is not
            # necessary as we won't receive that signal.
            windows_spawn_options = {
                "startupinfo": subprocess.STARTUPINFO(
                    dwFlags=subprocess.STARTF_USESHOWWINDOW,
                    wShowWindow=subprocess.SW_HIDE,
                ),
                "creationflags": subprocess.CREATE_NEW_CONSOLE,
            }

        # TODO: Always add --json-stream once 2.6.0 is minimum requirement
        if self.parsed_version >= (2, 6, 0):
            args.append("--json-stream")

        if solver is None:
            cmd = [str(self._executable), "--allow-multiple-assignments"] + [
                str(arg) for arg in args
            ]
            minizinc.logger.debug(f"CLIDriver:run -> command: \"{' '.join(cmd)}\"")
            output = subprocess.run(
                cmd,
                stdin=None,
                stdout=PIPE,
                stderr=PIPE,
                **windows_spawn_options,
            )
        else:
            with solver.configuration() as conf:
                cmd = [
                    str(self._executable),
                    "--solver",
                    conf,
                    "--allow-multiple-assignments",
                ] + [str(arg) for arg in args]
                minizinc.logger.debug(f"CLIDriver:run -> command: \"{' '.join(cmd)}\"")
                output = subprocess.run(
                    cmd,
                    stdin=None,
                    stdout=PIPE,
                    stderr=PIPE,
                    **windows_spawn_options,
                )
        if output.returncode != 0:
            if self.parsed_version >= (2, 6, 0):
                # Error will (usually) be raised in json stream
                for _ in decode_json_stream(output.stdout):
                    pass
            raise parse_error(output.stderr)
        return output

    async def _create_process(
        self, args: List[str], solver: Optional[str] = None
    ) -> Process:
        """Start an asynchronous driver process with given arguments

        Args:
            args (List[str]): direct arguments to the driver
            solver (Union[str, Path, None]): Solver configuration string
                guaranteed by the user to be valid until the process has ended.
        """

        windows_spawn_options: Dict[str, Any] = {}
        if sys.platform == "win32":
            # See corresponding comment in run()
            windows_spawn_options = {
                "startupinfo": subprocess.STARTUPINFO(
                    dwFlags=subprocess.STARTF_USESHOWWINDOW,
                    wShowWindow=subprocess.SW_HIDE,
                ),
                "creationflags": subprocess.CREATE_NEW_CONSOLE,
            }

        # TODO: Always add --json-stream once 2.6.0 is minimum requirement
        if self.parsed_version >= (2, 6, 0):
            args.append("--json-stream")

        if solver is None:
            minizinc.logger.debug(
                f"CLIDriver:create_process -> program: {str(self._executable)} "
                f'args: "--allow-multiple-assignments '
                f"{' '.join(str(arg) for arg in args)}\""
            )
            proc = await create_subprocess_exec(
                str(self._executable),
                "--allow-multiple-assignments",
                *[str(arg) for arg in args],
                stdin=None,
                stdout=PIPE,
                stderr=PIPE,
                **windows_spawn_options,
            )
        else:
            minizinc.logger.debug(
                f"CLIDriver:create_process -> program: {str(self._executable)} "
                f'args: "--solver {solver} --allow-multiple-assignments '
                f"{' '.join(str(arg) for arg in args)}\""
            )
            proc = await create_subprocess_exec(
                str(self._executable),
                "--solver",
                solver,
                "--allow-multiple-assignments",
                *[str(arg) for arg in args],
                stdin=None,
                stdout=PIPE,
                stderr=PIPE,
                **windows_spawn_options,
            )
        return proc

    @classmethod
    def find(
        cls, path: Optional[List[str]] = None, name: str = "minizinc"
    ) -> Optional["Driver"]:
        """Finds MiniZinc Driver on default or specified path.

        Find driver will look for the MiniZinc executable to create a Driver for
        MiniZinc Python. If no path is specified, then the paths given by the
        environment variables appended by MiniZinc's default locations will be tried.

        Args:
            path: List of locations to search.
            name: Name of the executable.

        Returns:
            Optional[Driver]: Returns a Driver object when found or None.
        """
        if path is None:
            path = os.environ.get("PATH", "").split(os.pathsep)
            # Add default MiniZinc locations to the path
            if platform.system() == "Darwin":
                path.extend(MAC_LOCATIONS)
            elif platform.system() == "Windows":
                path.extend(WIN_LOCATIONS)

        # Try to locate the MiniZinc executable
        executable = shutil.which(name, path=os.pathsep.join(path))
        if executable is not None:
            return cls(Path(executable))
        return None
