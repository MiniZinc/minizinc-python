#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at http://mozilla.org/MPL/2.0/.
import os
import platform
import shutil
import subprocess
from pathlib import Path
from typing import List, Optional, Union

from .driver import MAC_LOCATIONS, WIN_LOCATIONS
from .error import ConfigurationError, MiniZincError


class MznAnalyse:
    """Python interface to the mzn-analyse executable

    This tool is used to retrieve information about or transform a MiniZinc
    instance. This is used, for example, to  diverse solutions to the given
    MiniZinc instance using the given solver configuration.
    """

    _executable: Path

    def __init__(self, executable: Path):
        self._executable = executable
        if not self._executable.exists():
            raise ConfigurationError(
                f"No MiniZinc data annotator executable was found at '{self._executable}'."
            )

    @classmethod
    def find(
        cls, path: Optional[List[str]] = None, name: str = "mzn-analyse"
    ) -> Optional["MznAnalyse"]:
        """Finds the mzn-analyse executable on default or specified path.

        The find method will look for the mzn-analyse executable to create an
        interface for MiniZinc Python. If no path is specified, then the paths
        given by the environment variables appended by default locations will be
        tried.

        Args:
            path: List of locations to search. name: Name of the executable.

        Returns:
            Optional[MznAnalyse]: Returns a MznAnalyse object when found or None.
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

    def run(
        self,
        mzn_files: List[Path],
        args: List[str],
    ) -> None:
        # Do not change the order of the arguments 'inline-includes', 'remove-items:output', 'remove-litter' and 'get-diversity-anns'
        tool_run_cmd: List[Union[str, Path]] = [self._executable]

        tool_run_cmd.extend(mzn_files)
        tool_run_cmd.extend(args)

        # Extract the diversity annotations.
        proc = subprocess.run(
            tool_run_cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE
        )
        if proc.returncode != 0:
            raise MiniZincError(message=str(proc.stderr))
