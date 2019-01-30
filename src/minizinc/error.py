import re
from pathlib import Path
from typing import NamedTuple, Optional, Sequence


# TODO: Python 3.7 -> @dataclass
class Location(NamedTuple):
    file: Optional[Path]
    line: int = 0
    columns: Sequence = []

    @classmethod
    def unknown(cls):
        return cls(None)


class MiniZincError(Exception):
    """
    Exception raised for errors raised by the MiniZinc Driver
    Attributes:
        location -- file location of the error
        message -- explanation of the error
    """

    def __init__(self, location: Location, message: str):
        super().__init__(message)
        self.location = location


class EvaluationError(MiniZincError):
    pass


class MiniZincAssertionError(EvaluationError):
    pass


class MiniZincTypeError(MiniZincError):
    pass


def parse_error(error_txt: bytes) -> MiniZincError:
    error = MiniZincError
    if re.search(rb"MiniZinc: evaluation error:", error_txt):
        error = EvaluationError
        if re.search(rb"Assertion failed:", error_txt):
            error = MiniZincAssertionError
    elif re.search(rb"MiniZinc: type error:", error_txt):
        error = MiniZincTypeError

    location = Location.unknown()
    match = re.search(rb"([^\s]+):(\d+)(.(\d+)-(\d+))?:\s", error_txt)
    if match:
        columns = location.columns
        if match[3]:
            columns = range(int(match[4].decode()), int(match[5].decode()))
        location = Location(Path(match[1].decode()), int(match[2].decode()), columns)

    message = ""
    lst = error_txt.split(b"\n")
    if lst:
        while len(lst) > 1 and lst[-1] == b"":
            lst.pop()
        message = lst[-1].split(b"rror:", 1)[-1].strip()

    return error(location, message.decode())
