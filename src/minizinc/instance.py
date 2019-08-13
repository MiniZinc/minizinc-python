#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at http://mozilla.org/MPL/2.0/.
import contextlib
from abc import ABC, abstractmethod
from typing import Optional

from .model import Method, Model
from .solver import Solver


class Instance(Model, ABC):
    """Abstract representation of a MiniZinc instance in Python.
    """

    @abstractmethod
    def __init__(self, solver: Solver, model: Optional[Model] = None):
        super().__init__()

    @property
    @abstractmethod
    def method(self) -> Method:
        """Query the Method used by the Instance.

        Returns:
            Method: Method of the goal used by the Instance.
        """
        pass

    @abstractmethod
    def solve(self, *args, **kwargs):
        """Solves the Instance using its given solver configuration.

        Find the solutions to the given MiniZinc instance using the given solver
        configuration. First, the Instance will be ensured to be in a state
        where the solver specified in the solver configuration can understand
        the problem and then the solver will be requested to find the
        appropriate solution(s) to the problem.

        Args:
            timeout (Optional[timedelta]): Set the time limit for the process of
                solving the instance.
            nr_solutions (Optional[int]): The requested number of solution.
                (Only available on satisfaction problems and when the ``-n``
                flag is supported by the solver).
            processes (Optional[int]): Set the number of processes the solver
                can use. (Only available when the ``-p`` flag is supported by
                the solver).
            random_seed (Optional[int]): Set the random seed for solver. (Only
                available when the ``-r`` flag is supported by the solver).
            free_search (bool): Allow the solver to ignore the search definition
                within the instance. (Only available when the ``-f`` flag is
                supported by the solver).
            all_solutions (bool): Request to solver to find all solutions. (Only
                available on satisfaction problems and when the ``-n`` flag is
                supported by the solver)
            ignore_errors (bool): Do not raise exceptions, when an error occurs
                the ``Result.status`` will be ``ERROR``.
            **kwargs: Other flags to be passed onto the solver. ``--`` can be
                omitted in the name of the flag. If the type of the flag is
                Boolean, then its value signifies its occurrence.

        Returns:
            Result: object containing values assigned and statistical
                information.

        Raises:
            MiniZincError: An error occurred while compiling or solving the
                model instance.

        """
        pass

    @abstractmethod
    @contextlib.contextmanager
    def branch(self):  # TODO: Self reference
        """Create a branch of the current instance

        Branches from the current instance and yields a child instance. Any
        changes made to the child instance can not influence the current
        instance. WARNING: The branch method assumes that no changes will be
        made to the parent method while the child instance is still alive.
        Changes to the parent model are locked until the child method are
        destroyed.

        Yields:
            Instance: branched child instance

        """
        pass
