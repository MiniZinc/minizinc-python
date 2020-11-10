#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at http://mozilla.org/MPL/2.0/.
import asyncio
import contextlib
import sys
from abc import ABC, abstractmethod
from datetime import timedelta
from typing import Optional

from .model import Method, Model
from .solver import Solver


class Instance(Model, ABC):
    """Abstract representation of a MiniZinc instance in Python.

    Raises:
        MiniZincError: when an error occurs during the parsing or
            type checking of the model object.
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

    def solve(
        self,
        timeout: Optional[timedelta] = None,
        nr_solutions: Optional[int] = None,
        processes: Optional[int] = None,
        random_seed: Optional[int] = None,
        all_solutions: bool = False,
        intermediate_solutions: bool = False,
        free_search: bool = False,
        optimisation_level: Optional[int] = None,
        **kwargs,
    ):
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
                available on satisfaction problems and when the ``-a`` flag is
                supported by the solver)
            intermediate_solutions (bool): Request the solver to output any
                intermediate solutions that are found during the solving
                process. (Only available on optimisation problems and when the
                ``-a`` flag is supported by the solver)
            optimisation_level (Optional[int]): Set the MiniZinc compiler
                optimisation level.

                - 0: Disable optimisation
                - 1: Single pass optimisation (default)
                - 2: Flatten twice to improve flattening decisions
                - 3: Perform root-node-propagation
                - 4: Probe bounds of all variables at the root node
                - 5: Probe values of all variables at the root node

            **kwargs: Other flags to be passed onto the solver. ``--`` can be
                omitted in the name of the flag. If the type of the flag is
                Boolean, then its value signifies its occurrence.

        Returns:
            Tuple[Status, Optional[Union[List[Dict], Dict]], Dict]:
                tuple containing solving status, values assigned in the
                solution, and statistical information. If no solutions is found
                the second member of the tuple is ``None``.

        Raises:
            MiniZincError: An error occurred while compiling or solving the
                model instance.

        """
        coroutine = self.solve_async(
            timeout=timeout,
            nr_solutions=nr_solutions,
            processes=processes,
            random_seed=random_seed,
            all_solutions=all_solutions,
            intermediate_solutions=intermediate_solutions,
            free_search=free_search,
            optimisation_level=optimisation_level,
            **kwargs,
        )
        if sys.version_info >= (3, 7):
            if sys.platform == "win32":
                asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
            return asyncio.run(coroutine)
        else:
            if sys.platform == "win32":
                loop = asyncio.ProactorEventLoop()
            else:
                loop = asyncio.events.new_event_loop()

            try:
                asyncio.events.set_event_loop(loop)
                return loop.run_until_complete(coroutine)
            finally:
                asyncio.events.set_event_loop(None)
                loop.close()

    @abstractmethod
    async def solve_async(
        self,
        timeout: Optional[timedelta] = None,
        nr_solutions: Optional[int] = None,
        processes: Optional[int] = None,
        random_seed: Optional[int] = None,
        all_solutions=False,
        intermediate_solutions=False,
        free_search: bool = False,
        optimisation_level: Optional[int] = None,
        **kwargs,
    ):
        """Solves the Instance using its given solver configuration in a coroutine.

        This method returns a coroutine that finds solutions to the given
        MiniZinc instance. For more information regarding this methods and its
        arguments, see the documentation of :func:`~MiniZinc.Instance.solve`.

        Returns:
            Tuple[Status, Optional[Union[List[Dict], Dict]], Dict]:
                tuple containing solving status, values assigned, and
                statistical information.

        Raises:
            MiniZincError: An error occurred while compiling or solving the
                model instance.

        """
        pass

    @abstractmethod
    async def solutions(
        self,
        timeout: Optional[timedelta] = None,
        nr_solutions: Optional[int] = None,
        processes: Optional[int] = None,
        random_seed: Optional[int] = None,
        all_solutions=False,
        intermediate_solutions=False,
        free_search: bool = False,
        optimisation_level: Optional[int] = None,
        **kwargs,
    ):
        """An asynchronous generator for solutions of the MiniZinc instance.

        This method provides an asynchronous generator for the solutions of the
        MiniZinc instance. Every (intermediate) solution is yielded one at a
        time, the last item yielded from the generator will not contain a new
        solution, but will return the final Status and all remaining
        statistical values. For more information regarding this methods and its
        arguments, see the documentation of :func:`~MiniZinc.Instance.solve`.

        Yields:
            Tuple[Status, Optional[Dict], Dict]:
                tuple containing solving status, values assigned, and
                statistical information.

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
