from __future__ import annotations  # For the use of self-referencing type annotations

import json
import re
from datetime import timedelta
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
        if b"=====ERROR=====" in output:
            s = cls.ERROR
        elif b"=====UNKNOWN=====" in output:
            s = cls.UNKNOWN
        elif b"=====UNSATISFIABLE=====" in output:
            s = cls.UNSATISFIABLE
        elif b"=====UNSATorUNBOUNDED=====" in output or b"=====UNBOUNDED=====" in output:
            s = cls.UNBOUNDED
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
    instance: Instance
    complete: bool
    _solution: Union[Solution, List[Solution]]
    time: timedelta

    StatisticTypes = {
        "nodes": int,  # Number of search nodes
        "failures": int,  # Number of leaf nodes that were failed
        "restarts": int,  # Number of times the solver restarted the search
        "variables": int,  # Number of variables
        "intVariables": int,  # Number of integer variables created
        "boolVariables": int,  # Number of bool variables created
        "floatVariables": int,  # Number of float variables created
        "setVariables": int,  # Number of set variables created
        "propagators": int,  # Number of propagators created
        "propagations": int,  # Number of propagator invocations
        "peakDepth": int,  # Peak depth of search tree
        "nogoods": int,  # Number of nogoods created
        "backjumps": int,  # Number of backjumps
        "peakMem": float,  # Peak memory (in Mbytes)
        "initTime": timedelta,  # Initialisation time (in seconds)
        "solveTime": timedelta,  # Solving time (in seconds)
    }

    def __init__(self):
        self.status = Status.ERROR
        self.complete = False
        self.stats = {}

    @classmethod
    def from_process(cls, instance: Instance, proc: CompletedProcess) -> Result:
        res = cls()
        res.instance = instance

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
            time_us = int(float(match[1]) * 1000000)
            res.time = timedelta(milliseconds=time_us)
        # TODO: Handle other solutions

        matches = re.findall(rb"%%%mzn-stat (\w*)=(.*)", proc.stdout)
        for m in matches:
            res.set_stat(m[0].decode(), m[1].decode())

        return res

    def set_stat(self, name: str, value: str):
        tt = self.StatisticTypes.get(name, str)
        if tt is timedelta:
            time_us = int(float(value) * 1000000)
            self.stats[name] = timedelta(microseconds=time_us)
        else:
            self.stats[name] = tt(value)

    def __getitem__(self, item):
        if self.complete:  # TODO: Check if in output variables
            return self._solution.get(item)
        else:
            raise NotImplementedError  # TODO: fix error type

    @property
    def objective(self):
        if self.complete:
            return self._solution.get("_objective")
        else:
            raise NotImplementedError  # TODO: fix error type
