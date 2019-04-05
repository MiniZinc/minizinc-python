#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at http://mozilla.org/MPL/2.0/.

import json
import re
from datetime import timedelta
from enum import Enum
from subprocess import CompletedProcess
from typing import Dict, List, NamedTuple, Optional, Sequence, Union

from .error import MiniZincError, parse_error
from .instance import Instance, Method
from .json import MZNJSONDecoder
from .solver import Solver


class Status(Enum):
    """Enumeration to represent the status of the solving process.

    Attributes:
        ERROR: An error occurred during the solving process.
        UNKNOWN: No solutions have been found and search has terminated without exploring the whole search space.
        UNBOUNDED: The objective of the optimisation problem is unbounded.
        UNSATISFIABLE: No solutions have been found and the whole search space was explored.
        SATISFIED: A solution was found, but possibly not the whole search space was explored.
        ALL_SOLUTIONS: All solutions in the search space have been found.
        OPTIMAL_SOLUTION: A solution has been found that is optimal according to the objective.
    """
    ERROR = 0
    UNKNOWN = 1
    UNBOUNDED = 2
    UNSATISFIABLE = 3
    SATISFIED = 4
    ALL_SOLUTIONS = 5
    OPTIMAL_SOLUTION = 6

    @classmethod
    def from_output(cls, output: bytes, method: Method):
        """Determines the solving status from the output of a MiniZinc process

        Determines the solving status according to the standard status output strings defined by MiniZinc. The output of
        the MiniZinc will be scanned in a defined order to best determine the status of the solving process. UNKNOWN
        will be returned if no status can be determined.

        Args:
            output (bytes): the standard output of a MiniZinc process.
            method (Method): the objective method used in the optimisation problem.

        Returns:
            Status: Status that could be determined from the output.
        """
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

    def has_solution(self) -> bool:
        """Returns true if the status suggest that a solution has been found."""
        if self in [self.SATISFIED, self.ALL_SOLUTIONS, self.OPTIMAL_SOLUTION]:
            return True
        return False


class Solution(NamedTuple):
    """Representation of a MiniZinc solution in Python

    Attributes:
        assignments (Dict[str, Union[bool, float, int]]): Variable assignments made to form the solution
        objective (Optional[Union[float, int]]): Objective value of the solution
        statistics (Dict[str, Union[float, int, timedelta]]): Statistical information generated during the search for
            the Solution
    """
    assignments: Dict[str, Union[bool, float, int]] = {}
    objective: Optional[Union[float, int]] = None
    statistics: Dict[str, Union[float, int, timedelta]] = {}

    def __getitem__(self, key):
        """Overrides the default implementation of item access (obj[key]) to directly access the assignments."""
        if isinstance(key, str):
            return self.assignments.__getitem__(key)
        else:
            return super().__getitem__(key)


class Result:
    """Represents the result of the solving process of a MiniZinc.

    The result object will contain the solutions found during the solving process, statistics regarding the process,
    and a analysis of the solving process itself.

    Attributes:
        access_all (bool): When set to true the result object will allow access to all (intermediate) solutions. This
            attribute will automatically be set to true when using ``all_solutions`` or ``nr_solutions`` in the solving
            process.
        status (Status): The determined status of the solving process.
        instance (Instance): The instance for which the result object will offer solutions. This instance might have
            changed since the result object was created.
        complete (bool): Set to true when the solving process was determined to be complete.
    """
    access_all: bool
    status: Status
    instance: Instance
    complete: bool
    _solutions: List[Solution]

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
        self.error = None
        self.complete = False
        self.stats = {}
        self._solutions = []
        self.access_all = False

    @classmethod
    def from_process(cls, instance: Instance, proc: CompletedProcess, ignore_errors: bool = False):
        """Creates a Result object from the a CompletedProcess object.

        Creates and initialises a Result object from a CompletedProcess object generated during the solving process by
        the MiniZinc executable. The output of the process will be parsed and split into the solution output and the
        statistics generated by the process. The output is analysed to give more information about the result of the
        solving process.

        Args:
            instance (Instance): Instance on which the solving process was triggered.
            proc (CompletedProcess): The raw result of the process solving the MiniZinc instance.
            ignore_errors (bool): When set to True, no errors will be raised.

        Returns:
            Result: Result object created according to the information of the CompletedProcess object.

        Raises:
            MiniZincError: An error occurred within the solving process.
        """
        res = cls()
        res.instance = instance

        # Determine solving status
        if proc.returncode == 0:
            res.status = Status.from_output(proc.stdout, instance.method)
        else:
            res.status = Status.ERROR
            res.error = parse_error(proc.stderr)
            if not ignore_errors:
                raise res.error

        # Parse solution
        sol_stream = re.split(rb"----------|==========", proc.stdout)
        for raw_sol in sol_stream:
            sol_json = re.sub(rb"^\w*%.*\n?", b"", raw_sol, flags=re.MULTILINE)
            if b"{" not in sol_json:
                continue
            dict = json.loads(sol_json, cls=MZNJSONDecoder)
            asgn = {}
            objective = None
            stats = {}
            for k, v in dict.items():
                if not k.startswith("_"):
                    asgn[k] = v
                elif k == "_objective":
                    objective = v
            match = re.search(rb"% time elapsed: (\d+.\d+) s", raw_sol)
            if match:
                time_us = int(float(match[1]) * 1000000)
                stats["time"] = timedelta(microseconds=time_us)
            res._solutions.append(Solution(asgn, objective, stats))

        matches = re.findall(rb"%%%mzn-stat:? (\w*)=(.*)", proc.stdout)
        for m in matches:
            res.set_stat(m[0].decode(), m[1].decode())

        # Determine if the solver completed all work
        if instance.method == Method.SATISFY:
            if '-a' in proc.args:  # TODO: Use the number of solutions
                res.complete = (res.status == Status.ALL_SOLUTIONS)
                res.access_all = True
            if '-n' in proc.args:
                n = int(proc.args[proc.args.index('-n') + 1])
                res.complete = (len(res._solutions) == n)
                res.access_all = True
            else:
                res.complete = (res.status == Status.SATISFIED)
        else:
            res.complete = (res.status == Status.OPTIMAL_SOLUTION)

        return res

    def check(self, solver: Solver, solution_nrs: Optional[Sequence[int]] = None) -> bool:
        """Checks the result of the solving process using a solver.

        Check the correctness of the solving process using a (different) solver configuration. An instance is branched
        and will be assigned all available values from a solution. The solver configuration is now used to confirm is
        assignment of the variables is correct. By default only the last solution will be checked. A sequence of
        solution numbers can be provided to check multiple solutions.

        Args:
            solver (Solver): The solver configuration used to check the solutions.
            solution_nrs: The index set of solutions to be checked. (default: [-1])

        Returns:
            bool: True if the given solution are correctly verified.
        """
        if solution_nrs is None:
            solution_nrs = [-1]

        for i in solution_nrs:
            sol = self._solutions[i]
            with self.instance.branch() as instance:
                instance._solver = solver  # TODO: This is not allowed behaviour
                for k, v in sol.assignments.items():
                    instance[k] = v
                try:
                    res = instance.solve(timeout=timedelta(seconds=1))
                    if self.status != res.status:
                        if res.status in [Status.SATISFIED, Status.OPTIMAL_SOLUTION] and \
                                self.status in [Status.SATISFIED, Status.OPTIMAL_SOLUTION, Status.ALL_SOLUTIONS]:
                            continue
                        else:
                            return False
                except MiniZincError:
                    if self.status != Status.ERROR:
                        return False

        return True

    def set_stat(self, name: str, value: str):
        """Set statistical value in the result object.

        Set solving statiscal value within the result object. This value is converted from string to the appropriate
        type as suggested by the statistical documentation in MiniZinc. Timing statistics, expressed through floating
        point numbers in MiniZinc, will be converted to timedelta objects.

        Args:
            name: The name under which the statistical value will be stored.
            value: The value for the statistical value to be converted and stored.
        """
        tt = self.StatisticTypes.get(name, str)
        if tt is timedelta:
            time_us = int(float(value) * 1000000)
            self.stats[name] = timedelta(microseconds=time_us)
        else:
            self.stats[name] = tt(value)

    def __getitem__(self, key):
        """Retrieves solution or a member of a solution.

        Overrides the default implementation of item access (obj[key]) to retrieve a solution or member of a solution
        from the result object. If the result object does not contain any solutions, then a KeyError will always be
        raised. If ``access_all`` is set to True, then multiple solutions can be accessed and this method can be used to
        retrieve a specified solution dictionary. Otherwise, the method will retrieve a value from the solution itself.

        Args:
            key: solution number or name of the solution member.

        Returns:
            solution dictionary or the value of the member in the solution.

        Raises:
            KeyError: No solution was found, solution number is out of range, or no solution member with this name
                exists.
        """
        if self.status.has_solution():
            if self.access_all:
                return self._solutions.__getitem__(key)
            else:
                return self._solutions[-1].__getitem__(key)
        else:
            raise KeyError

    def __len__(self):
        """Returns the number of solutions that can be accessed

        Returns the number of solutions that can currently be accessed. When ``access_all`` is set to False only 0 or 1
        can be returned. If this is not the case, then the number of solutions found will be returned. Note for
        optimisation problems this will include the intermediate results.

        Returns:
            int: number of solution that can be accessed
        """
        if self.access_all:
            return self._solutions.__len__()
        else:
            return 1 if self.status.has_solution() else 0

    @property
    def objective(self) -> Optional[Union[int, float]]:
        """Returns best objective found

        Returns the best object found when possible. If no solutions have been found or the problem did not have an
        objective, then None is returned instead.

        Returns:
            Optional[Union[int, float]]: best objective found or None
        """
        if self.status.has_solution() and self.instance.method != Method.SATISFY:
            return self._solutions[-1].objective
        else:
            return None
