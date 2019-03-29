#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at http://mozilla.org/MPL/2.0/.

import re
from pathlib import Path
from typing import NamedTuple, Optional, Tuple


# TODO: Python 3.7 -> @dataclass
class Location(NamedTuple):
    """Representation of a location within a file

    Attributes:
        file (Optional[Path]): Path to the file
        line (int): Line within the file (default: 0)
        columns (Tuple[int,int]): Columns on the line, from/to (default: (0, 0))
    """
    file: Optional[Path]
    line: int = 0
    columns: Tuple[int, int] = (0, 0)


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


class EvaluationError(MiniZincError):
    """Exception raised for errors due to an error during instance evaluation by the MiniZinc Driver"""
    pass


class MiniZincAssertionError(EvaluationError):
    """Exception raised for MiniZinc assertions that failed during instance evaluation"""
    pass


class MiniZincTypeError(MiniZincError):
    """Exception raised for type errors found in an MiniZinc Instance"""
    pass


class MiniZincSyntaxError(MiniZincError):
    """Exception raised for syntax errors found in an MiniZinc Instance"""
    pass


def parse_error(error_txt: bytes) -> MiniZincError:
    """Parse error from bytes array (raw string)

    Parse error scans the output from a MiniZinc driver to generate the appropriate MiniZincError. It will make the
    distinction between different kinds of errors as found by MiniZinc and tries to parse the relevant information to
    the error. The different kinds of errors are represented by different sub-classes of MiniZincError.

    Args:
        error_txt (bytes): raw string containing a MiniZinc error. Generally this should be the error stream of a
            driver.

    Returns:
        An error generated from the string
    """
    error = MiniZincError
    if b"MiniZinc: evaluation error:" in error_txt:
        error = EvaluationError
        if b"Assertion failed:" in error_txt:
            error = MiniZincAssertionError
    elif b"MiniZinc: type error:" in error_txt:
        error = MiniZincTypeError
    elif b"Error: syntax error" in error_txt:
        error = MiniZincSyntaxError

    location = None
    match = re.search(rb"([^\s]+):(\d+)(.(\d+)-(\d+))?:\s", error_txt)
    if match:
        columns = (0, 0)
        if match[3]:
            columns = (int(match[4].decode()), int(match[5].decode()))
        location = Location(Path(match[1].decode()), int(match[2].decode()), columns)

    message = ""
    lst = error_txt.split(b"\n")
    if lst:
        while len(lst) > 1 and lst[-1] == b"":
            lst.pop()
        message = lst[-1].split(b"rror:", 1)[-1].strip()

    return error(location, message.decode())
