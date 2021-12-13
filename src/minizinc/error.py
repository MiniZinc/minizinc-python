#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at http://mozilla.org/MPL/2.0/.

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple


@dataclass
class Location:
    """Representation of a location within a file

    Attributes:
        file (Optional[Path]): Path to the file
        line (int): Line within the file (default: ``0``)
        columns (Tuple[int,int]): Columns on the line, from/to (default:
            ``(0, 0)``)

    """

    file: Optional[Path]
    lines: Tuple[int, int] = (0, 0)
    columns: Tuple[int, int] = (0, 0)


class ConfigurationError(Exception):
    """Exception raised during the configuration of MiniZinc

    Attributes:
        message (str): Explanation of the error
    """

    message: str


class MiniZincError(Exception):
    """Exception raised for errors caused by a MiniZinc Driver

    Attributes:
        location (Optional[Location]): File location of the error
        message (str): Explanation of the error
    """

    location: Optional[Location]
    message: str

    def __init__(self, location: Optional[Location] = None, message: str = ""):
        super().__init__(message)
        self.location = location


class MiniZincWarning(Warning):
    """Warning created for warnings originating from a MiniZinc Driver"""


class EvaluationError(MiniZincError):
    """Exception raised for errors due to an error during instance evaluation by
    the MiniZinc Driver"""

    pass


class AssertionError(EvaluationError):
    """Exception raised for MiniZinc assertions that failed during instance
    evaluation"""

    pass


class TypeError(MiniZincError):
    """Exception raised for type errors found in an MiniZinc Instance"""

    pass


class IncludeError(MiniZincError):
    """Exception raised for type errors found in an MiniZinc Instance"""

    pass


class CyclicIncludeError(MiniZincError):
    """Exception raised for type errors found in an MiniZinc Instance"""

    pass


class SyntaxError(MiniZincError):
    """Exception raised for syntax errors found in an MiniZinc Instance"""

    pass


def parse_error(error_txt: bytes) -> MiniZincError:
    """Parse error from bytes array (raw string)

    Parse error scans the output from a MiniZinc driver to generate the
    appropriate MiniZincError. It will make the distinction between different
    kinds of errors as found by MiniZinc and tries to parse the relevant
    information to the error. The different kinds of errors are represented by
    different sub-classes of MiniZincError.

    Args:
        error_txt (bytes): raw string containing a MiniZinc error. Generally
            this should be the error stream of a driver.

    Returns:
        An error generated from the string

    """
    error = MiniZincError
    if b"MiniZinc: evaluation error:" in error_txt:
        error = EvaluationError
        if b"Assertion failed:" in error_txt:
            error = AssertionError
    elif b"MiniZinc: type error:" in error_txt:
        error = TypeError
    elif b"Error: syntax error" in error_txt:
        error = SyntaxError

    location = None
    match = re.search(rb"([^\s]+):(\d+)(.(\d+)-(\d+))?:\s", error_txt)
    if match:
        columns = (0, 0)
        if match[3]:
            columns = (int(match[4].decode()), int(match[5].decode()))
        lines = (int(match[2].decode()), int(match[2].decode()))
        location = Location(Path(match[1].decode()), lines, columns)

    message = error_txt.decode().strip()
    if not message:
        message = (
            "MiniZinc stopped with a non-zero exit code, but did not output an "
            "error message. "
        )
    elif location is not None and location.file is not None and location.file.exists():
        with location.file.open() as f:
            for _ in range(location.line - 2):
                f.readline()
            message += "\nFile fragment:\n"
            for nr in range(max(1, location.line - 1), location.line + 2):
                line = f.readline()
                if line == "":
                    break
                message += f"{nr}: {line.rstrip()}\n"
                diff = location.columns[1] - location.columns[0]
                if nr == location.line and diff > 0:
                    message += (
                        " " * (len(str(nr)) + 2 + location.columns[0] - 1)
                        + "^" * (diff + 1)
                        + "\n"
                    )

    return error(location, message)


def error_from_stream_obj(obj):
    """Convert object from JSON stream into MiniZinc Python error

    Args:
        obj (Dict): Parsed JSON object from the ``--json-stream``
            mode of MiniZinc.

    Returns:
        An error generated from the object

    """
    assert obj["type"] == "error"
    error = MiniZincError
    if obj["what"] == "syntax error":
        error = SyntaxError
    elif obj["what"] == "type error":
        error = TypeError
    elif obj["what"] == "include error":
        error = IncludeError
    elif obj["what"] == "cyclic include error":
        error = CyclicIncludeError
    elif obj["what"] == "evaluation error":
        error = EvaluationError
    elif obj["what"] == "assertion failed":
        error = AssertionError

    location = None
    if "location" in obj:
        location = Location(
            obj["location"]["filename"],
            (obj["location"]["firstLine"], obj["location"]["lastLine"]),
            (obj["location"]["firstColumn"], obj["location"]["lastColumn"]),
        )

    # TODO: Process stack information

    return error(location, obj["message"])
