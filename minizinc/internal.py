import re
import shutil
import subprocess

from ctypes import cdll, CDLL

#: MiniZinc version required by the python package
required_version = (2, 2, 0)

#: Default executable used by the python package
default_executable = None
try:
    # Try to load the MiniZinc C API
    default_executable = cdll.LoadLibrary("minizinc")
except OSError:
    # Try to locate the MiniZinc executable
    default_executable = shutil.which("minizinc")


def _is_library(elem) -> bool:
    """
    Returns true if elem is an library format
    """
    return isinstance(elem, CDLL)


def _version(minizinc=default_executable) -> tuple:
    """
    Returns a tuple containing the semantic version of the MiniZinc version given
    :param minizinc: path to the minizinc executable or CDLL library
    :return: tuple containing the minizinc version or None
    """
    if _is_library(minizinc):
        raise NotImplementedError()
    elif minizinc is not None:
        output = subprocess.run([minizinc, "--version"], capture_output=True, check=True)
        match = re.search(r'version (\d+)\.(\d+)\.(\d+)', output.stdout.decode())
        return tuple([int(i) for i in match.groups()])
    else:
        raise FileNotFoundError


# Check compatibility of the MiniZinc version
if _version() < required_version:
    raise ImportWarning("Unsupported MiniZinc version, minimal required version %d.%d.%d (found %d.%d.%d)"
                        % (required_version + _version()))
