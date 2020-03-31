#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at http://mozilla.org/MPL/2.0/.

import json
import re
from dataclasses import dataclass
from datetime import timedelta
from enum import Enum, auto
from keyword import kwlist
from typing import Any, Dict, Optional, Tuple, Type, Union

from .instance import Method
from .json import MZNJSONDecoder

StatisticsType = Union[float, int, str, timedelta]

StdStatisticTypes = {
    # Number of search nodes
    "nodes": int,
    # Number of leaf nodes that were failed
    "failures": int,
    # Number of times the solver restarted the search
    "restarts": int,
    # Number of variables
    "variables": int,
    # Number of integer variables created by the solver
    "intVariables": int,
    # Number of Boolean variables created by the solver
    "boolVariables": int,
    # Number of floating point variables created by the solver
    "floatVariables": int,
    # Number of set variables created by the solver
    "setVariables": int,
    # Number of propagators created by the solver
    "propagators": int,
    # Number of propagator invocations
    "propagations": int,
    # Peak depth of search tree
    "peakDepth": int,
    # Number of nogoods created
    "nogoods": int,
    # Number of backjumps
    "backjumps": int,
    # Peak memory (in Mbytes)
    "peakMem": float,
    # Initialisation time
    "initTime": timedelta,
    # Solving time
    "solveTime": timedelta,
    # Flattening time
    "flatTime": timedelta,
    # Number of paths generated
    "paths": int,
    # Number of Boolean variables in the flat model
    "flatBoolVars": int,
    # Number of floating point variables in the flat model
    "flatFloatVars": int,
    # Number of integer variables in the flat model
    "flatIntVars": int,
    # Number of set variables in the flat model
    "flatSetVars": int,
    # Number of Boolean constraints in the flat model
    "flatBoolConstraints": int,
    # Number of floating point constraints in the flat model
    "flatFloatConstraints": int,
    # Number of integer constraints in the flat model
    "flatIntConstraints": int,
    # Number of set constraints in the flat model
    "flatSetConstraints": int,
    # Optimisation method in the Flat Model
    "method": str,
    # Number of reified constraints evaluated during flattening
    "evaluatedReifiedConstraints": int,
    # Number of half-reified constraints evaluated during flattening
    "evaluatedHalfReifiedConstraints": int,
    # Number of implications removed through chain compression
    "eliminatedImplications": int,
    # Number of linear constraints removed through chain compression
    "eliminatedLinearConstraints": int,
}


def set_stat(stats: Dict[str, StatisticsType], name: str, value: str):
    """Set statistical value in the result object.

    Set solving statiscal value within the result object. This value is
    converted from string to the appropriate type as suggested by the
    statistical documentation in MiniZinc. Timing statistics, expressed through
    floating point numbers in MiniZinc, will be converted to timedelta objects.

    Args:
        stats: The dictionary to be extended with the new statistical value
        name: The name under which the statistical value will be stored.
        value: The value for the statistical value to be converted and stored.

    """
    value = value.strip('"')
    tt = StdStatisticTypes.get(name, None)
    if tt is timedelta or (tt is None and ("time" in name or "Time" in name)):
        time_us = int(float(value) * 1000000)
        stats[name] = timedelta(microseconds=time_us)
    elif tt is not None:
        stats[name] = tt(value)
    else:
        try:
            stats[name] = int(value)
            return
        except ValueError:
            try:
                stats[name] = float(value)
                return
            except ValueError:
                stats[name] = value


class Status(Enum):
    """Enumeration to represent the status of the solving process.

    Attributes:
        ERROR: An error occurred during the solving process.
        UNKNOWN: No solutions have been found and search has terminated without
            exploring the whole search space.
        UNBOUNDED: The objective of the optimisation problem is unbounded.
        UNSATISFIABLE: No solutions have been found and the whole search space
            was explored.
        SATISFIED: A solution was found, but possibly not the whole search
            space was explored.
        ALL_SOLUTIONS: All solutions in the search space have been found.
        OPTIMAL_SOLUTION: A solution has been found that is optimal according
            to the objective.

    """

    ERROR = auto()
    UNKNOWN = auto()
    UNBOUNDED = auto()
    UNSATISFIABLE = auto()
    SATISFIED = auto()
    ALL_SOLUTIONS = auto()
    OPTIMAL_SOLUTION = auto()

    @classmethod
    def from_output(cls, output: bytes, method: Method):
        """Determines the solving status from the output of a MiniZinc process

        Determines the solving status according to the standard status output
        strings defined by MiniZinc. The output of the MiniZinc will be scanned
        in a defined order to best determine the status of the solving process.
        UNKNOWN will be returned if no status can be determined.

        Args:
            output (bytes): the standard output of a MiniZinc process.
            method (Method): the objective method used in the optimisation
                problem.

        Returns:
            Optional[Status]: Status that could be determined from the output.

        """
        s = None
        if b"=====ERROR=====" in output:
            s = cls.ERROR
        elif b"=====UNKNOWN=====" in output:
            s = cls.UNKNOWN
        elif b"=====UNSATISFIABLE=====" in output:
            s = cls.UNSATISFIABLE
        elif (
            b"=====UNSATorUNBOUNDED=====" in output or b"=====UNBOUNDED=====" in output
        ):
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

    def __str__(self):
        return self.name

    def has_solution(self) -> bool:
        """Returns true if the status suggest that a solution has been found."""
        if self in [self.SATISFIED, self.ALL_SOLUTIONS, self.OPTIMAL_SOLUTION]:
            return True
        return False


@dataclass
class Result:
    """Representation of a MiniZinc solution in Python

    Attributes:
        status (Status): The solving status of the MiniZinc instance
        solution (Any): Variable assignments
            made to form the solution
        statistics (Dict[str, Union[float, int, timedelta]]): Statistical
            information generated during the search for the Solution

    """

    status: Status
    solution: Any
    statistics: Dict[str, Union[float, int, timedelta]]

    @property
    def objective(self) -> Optional[Union[int, float]]:
        """Returns objective of the solution

        Returns the objective of the solution when possible. If no solutions
        have been found or the problem did not have an objective, then None is
        returned instead.

        Returns:
            Optional[Union[int, float]]: best objective found or None

        """
        if self.solution is not None:
            if isinstance(self.solution, list):
                return getattr(self.solution[-1], "objective", None)
            else:
                return getattr(self.solution, "objective", None)
        else:
            return None

    def __getitem__(self, key):
        """Retrieves solution or a member of a solution.

        Overrides the default implementation of item access (obj[key]) to
        retrieve a solution object or member of a solution from the result
        object.

        - If the Result object does not contain any solutions, then a
          KeyError will always be raised.
        - If the Result object contains a single solutions, then the names of a
          variable can be used in this method to retrieve its value in the
          solution.
        - If the Result object contains multiple solutions, then a single
          integer can be used to retrieve the solution object or a tuple of an
          integer and the name of a variable can be used to retrieve the value
          of that variable in the numbered solution object.

        Args:
            key: solution number or name of the solution member.

        Returns:
            Solution object or the value of the member in the solution.

        Raises:
            KeyError: No solution was found, solution number is out of range,
                or no solution member with this name exists.

        """
        try:
            if self.solution is not None:
                if isinstance(self.solution, list):
                    if isinstance(key, tuple):
                        return getattr(self.solution.__getitem__(key[0]), key[1])
                    else:
                        return self.solution.__getitem__(key)
                else:
                    return getattr(self.solution, key)
            else:
                raise KeyError
        except AttributeError:
            raise KeyError

    def __len__(self):
        """Returns the number of solutions included in the Result object

        Returns:
            int: number of solution that can be accessed

        """
        if self.solution is None:
            return 0
        elif isinstance(self.solution, list):
            return len(self.solution)
        else:
            return 1

    def __str__(self):
        return str(self.solution)


def parse_solution(
    raw: bytes, output_type: Type, enum_map: Dict[str, Enum]
) -> Tuple[Optional[Any], Dict]:
    """Parses a solution from the output of a MiniZinc process.

    Parses the MiniZinc output between solution separators. The solution is
    expected to be formatted according to the MiniZinc JSON standards.
    Statistical information can be included in the output in accordance with
    the MiniZinc statistics standard. Statistics will be parsed and retyped
    according to the types given in StatisticTypes. Statistics will be parsed
    even if no solution is found.

    Args:
        raw (bytes): The output on stdout for one solution of the process
            solving the MiniZinc instance.
        output_type (Type): The type used for every solution
        enum_map (Dict[str, Enum]): A map to map enumeration identifiers to
            the internal values used in Python

    Returns:
        Tuple[Optional[Dict], Dict]: A tuple containing the parsed solution
            assignments and the parsed statistics.

    """
    # Parse statistics
    statistics: Dict[str, StatisticsType] = {}
    matches = re.findall(rb"%%%mzn-stat:? (\w*)=([^\r\n]*)", raw)
    for m in matches:
        set_stat(statistics, m[0].decode(), m[1].decode())
    match = re.search(rb"% time elapsed: (\d+.\d+) s", raw)
    if match:
        time_us = int(float(match[1]) * 1000000)
        statistics["time"] = timedelta(microseconds=time_us)

    # Parse solution
    solution = None
    raw = re.sub(
        rb"^-{10}|={5}(ERROR|UNKNOWN|UNSATISFIABLE|UNSATorUNBOUNDED|UNBOUNDED|)?={5}",
        b"",
        raw,
        flags=re.MULTILINE,
    )
    raw = re.sub(rb"^\w*%.*\n?", b"", raw, flags=re.MULTILINE)
    if b"{" in raw:
        tmp = json.loads(raw, enum_map=enum_map, cls=MZNJSONDecoder)
        if "_objective" in tmp:
            tmp["objective"] = tmp.pop("_objective")
        if "_output" in tmp:
            tmp["_output_item"] = tmp.pop("_output")
        for k in kwlist:
            if k in tmp:
                tmp["mzn_" + k] = tmp.pop(k)

        solution = output_type(**tmp)

    return solution, statistics
