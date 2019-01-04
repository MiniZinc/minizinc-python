from __future__ import annotations  # For the use of self-referencing type annotations

import datetime
import json
import re
from enum import Enum
from subprocess import CompletedProcess
from typing import Union, Dict, List

from .model import Method, Instance

Solution = Dict[str, Union[float, int, bool]]


class Status(Enum):
    ERROR = 0
    UNKNOWN = 1
    UNBOUNDED = 2
    UNSATISFIABLE = 3
    SATISFIED = 4
    ALL_SOLUTIONS = 5
    OPTIMAL_SOLUTION = 6

    @classmethod
    def from_output(cls, output, method):
        s = cls.UNKNOWN
        if b"=====UNSATISFIABLE=====" in output:
            s = cls.UNSATISFIABLE
        elif b"=====UNSATorUNBOUNDED=====" in output or b"=====UNBOUNDED=====" in output:
            s = cls.UNBOUNDED
        elif b"=====ERROR=====" in output:
            s = cls.ERROR
        elif b"=====UNKNOWN=====" in output:
            s = cls.UNKNOWN
        elif method is Method.SATISFY:
            if b"==========" in output:
                s = cls.ALL_SOLUTIONS
            elif b"----------" in output:
                s = cls.SATISFIED
        else:
            if b"==========" in output:
                s = cls.OPTIMAL_SOLUTION
            elif b"----------" in output:
                s = cls.SATISFIED
        return s


class Result:
    status: Status
    complete: bool
    _solution: Union[Solution, List[Solution]]
    solution_time: datetime.timedelta

    def __init__(self):
        self.status = Status.ERROR
        self.complete = False

    def __getitem__(self, item):
        if self.complete:
            return self._solution.get(item)
        else:
            raise NotImplementedError  # TODO: fix error type

    @classmethod
    def from_process(cls, instance: Instance, proc: CompletedProcess) -> Result:
        res = cls()

        # Determine solving status
        if proc.returncode == 0:
            res.status = Status.from_output(proc.stdout, instance.method)
        else:
            res.status = Status.ERROR

        # Determine if the solver completed all work
        if instance.method == Method.SATISFY:
            if '-a' in proc.args:  # TODO: Use the number of solutions
                res.complete = (res.status == Status.ALL_SOLUTIONS)
            else:
                res.complete = (res.status == Status.SATISFIED)
        else:
            res.complete = (res.status == Status.OPTIMAL_SOLUTION)

        # Parse solution
        sol_stream = proc.stdout.split(b"----------")
        del sol_stream[-1]
        sol_json = re.sub(rb"^\w*%.*\n?", b"", sol_stream[-1], flags=re.MULTILINE)
        res._solution = json.loads(sol_json)
        match = re.search(rb"% time elapsed: (\d+.\d+) s", sol_stream[-1])
        if match:
            time_ms = int( float(match[1]) * 1000 )
            res.solution_time = datetime.timedelta(milliseconds=time_ms)
        # TODO: Handle other solutions

        return res
