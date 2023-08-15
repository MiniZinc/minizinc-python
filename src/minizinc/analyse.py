#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at http://mozilla.org/MPL/2.0/.
import json
import os
import platform
import shutil
import subprocess
from enum import Enum, auto
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .driver import MAC_LOCATIONS, WIN_LOCATIONS
from .error import ConfigurationError, MiniZincError


class InlineOption(Enum):
    DISABLED = auto()
    NON_LIBRARY = auto()
    ALL = auto()


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
        inline_includes: InlineOption = InlineOption.DISABLED,
        remove_litter: bool = False,
        get_diversity_anns: bool = False,
        get_solve_anns: bool = True,
        output_all: bool = True,
        mzn_output: Optional[Path] = None,
        remove_anns: Optional[List[str]] = None,
        remove_items: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        # Do not change the order of the arguments 'inline-includes', 'remove-items:output', 'remove-litter' and 'get-diversity-anns'
        tool_run_cmd: List[Union[str, Path]] = [str(self._executable), "json_out:-"]

        for f in mzn_files:
            tool_run_cmd.append(str(f))

        if inline_includes == InlineOption.ALL:
            tool_run_cmd.append("inline-all_includes")
        elif inline_includes == InlineOption.NON_LIBRARY:
            tool_run_cmd.append("inline-includes")

        if remove_items is not None and len(remove_items) > 0:
            tool_run_cmd.append(f"remove-items:{','.join(remove_items)}")
        if remove_anns is not None and len(remove_anns) > 0:
            tool_run_cmd.append(f"remove-anns:{','.join(remove_anns)}")

        if remove_litter:
            tool_run_cmd.append("remove-litter")
        if get_diversity_anns:
            tool_run_cmd.append("get-diversity-anns")

        if mzn_output is not None:
            tool_run_cmd.append(f"out:{str(mzn_output)}")
        else:
            tool_run_cmd.append("no_out")

        # Extract the diversity annotations.
        proc = subprocess.run(
            tool_run_cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE
        )
        if proc.returncode != 0:
            raise MiniZincError(message=str(proc.stderr))
        return json.loads(proc.stdout)
