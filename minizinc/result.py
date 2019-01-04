from __future__ import annotations  # For the use of self-referencing type annotations

from enum import Enum
from subprocess import CompletedProcess

from .model import Method


class Status(Enum):
    ERROR = 0
    UNKNOWN = 1
    SATISFIED = 2
    COMPLETE = 3
    INVALID = 4


class Result:
    def __init__(self):
        self.status: Status = Status.ERROR

    @classmethod
    def from_process(cls, proc: CompletedProcess, method: Method) -> Result:
        return Result()  # TODO
