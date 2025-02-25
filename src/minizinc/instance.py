#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at http://mozilla.org/MPL/2.0/.
import asyncio
import contextlib
import json
import logging
import os
import re
import sys
import tempfile
import warnings
from dataclasses import asdict, field, is_dataclass, make_dataclass
from datetime import timedelta
from enum import EnumMeta
from keyword import iskeyword
from numbers import Number
from pathlib import Path
from typing import (
    Any,
    AsyncIterator,
    Dict,
    Iterator,
    List,
    Optional,
    Set,
    Tuple,
    Type,
    Union,
)

import minizinc

from .analyse import InlineOption, MznAnalyse
from .driver import Driver
from .error import ConfigurationError, MiniZincError, parse_error
from .json import (
    MZNJSONDecoder,
    MZNJSONEncoder,
    decode_async_json_stream,
    decode_json_stream,
)
from .model import Method, Model, ParPath, UnknownExpression
from .result import Result, Status, set_stat
from .solver import Solver

if sys.version_info >= (3, 8):
    from typing import Final

    SEPARATOR: Final[bytes] = str.encode("----------" + os.linesep)
else:
    SEPARATOR: bytes = str.encode("----------" + os.linesep)


class _GeneratedSolution:
    pass


class Instance(Model):
    """Representation of a MiniZinc instance in Python.

    Raises:
        MiniZincError: when an error occurs during the parsing or
            type checking of the model object.
    """

    _driver: Driver
    _solver: Solver
    _input_cache: Optional[Dict[str, Type]] = None
    _output_cache: Optional[Dict[str, Type]] = None
    _method_cache: Optional[Method] = None
    _has_output_item_cache: Optional[bool] = None
    _parent: Optional["Instance"] = None
    _field_renames: List[Tuple[str, str]]

    def __init__(
        self,
        solver: Solver,
        model: Optional[Model] = None,
        driver: Optional[Driver] = None,
    ):
        super().__init__()
        self._solver = solver
        self._field_renames = []
        if driver is not None:
            self._driver = driver
        elif minizinc.default_driver is not None:
            self._driver = minizinc.default_driver
        else:
            raise Exception("No compatible driver provided")

        if model is not None:
            self.output_type = model.output_type
            self._includes = model._includes.copy()
            self._code_fragments = model._code_fragments.copy()
            self._data = dict.copy(model._data)
            self._enum_map = dict.copy(model._enum_map)
            self._checker = True

            # Generate output_type to ensure the same type between different
            # instances of the same model
            if self.output_type is None:
                self.analyse()
                model.output_type = self.output_type

    def solve(
        self,
        time_limit: Optional[timedelta] = None,
        nr_solutions: Optional[int] = None,
        processes: Optional[int] = None,
        random_seed: Optional[int] = None,
        all_solutions: bool = False,
        intermediate_solutions: Optional[bool] = None,
        free_search: bool = False,
        optimisation_level: Optional[int] = None,
        timeout: Optional[timedelta] = None,
        **kwargs,
    ) -> Result:
        """Solves the Instance using its given solver configuration.

        Find the solutions to the given MiniZinc instance using the given solver
        configuration. First, the Instance will be ensured to be in a state
        where the solver specified in the solver configuration can understand
        the problem and then the solver will be requested to find the
        appropriate solution(s) to the problem.

        Args:
            time_limit (Optional[timedelta]): Set the time limit for the process of
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
            intermediate_solutions (Optional[bool]): Request the solver to
                output any intermediate solutions that are found during the
                solving process. If left to ``None``, then intermediate
                solutions might still be requested to ensure that the solving
                process gives its final solution. (Only available on
                optimisation problems and when the ``-i`` or ``-a`` flag is
                supported by the solver)
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
            time_limit=time_limit,
            nr_solutions=nr_solutions,
            processes=processes,
            random_seed=random_seed,
            all_solutions=all_solutions,
            intermediate_solutions=intermediate_solutions,
            free_search=free_search,
            optimisation_level=optimisation_level,
            timeout=timeout,
            **kwargs,
        )
        try:
            if sys.platform == "win32":
                asyncio.set_event_loop_policy(
                    asyncio.WindowsProactorEventLoopPolicy()
                )
            return asyncio.run(coroutine)
        except RuntimeError as r:
            coroutine.close()
            del coroutine
            if "called from a running event loop" in r.args[0]:
                raise RuntimeError(
                    "the synchronous MiniZinc Python `solve()` method was called from"
                    " an asynchronous environment.\n\nBecause Python's asyncio library"
                    " does not support using multiple event loops that would be"
                    " required to use this method, we instead suggest you use the"
                    " `solve_async()' method or patch Python behaviour with a package"
                    " such as `nested_asyncio'.\n\nOriginal message: " + str(r)
                ) from r
            else:
                raise r

    async def solve_async(
        self,
        time_limit: Optional[timedelta] = None,
        nr_solutions: Optional[int] = None,
        processes: Optional[int] = None,
        random_seed: Optional[int] = None,
        all_solutions: bool = False,
        intermediate_solutions: Optional[bool] = None,
        free_search: bool = False,
        optimisation_level: Optional[int] = None,
        timeout: Optional[timedelta] = None,
        **kwargs,
    ) -> Result:
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
        status = Status.UNKNOWN
        statistics: Dict[str, Any] = {}

        multiple_solutions = (
            all_solutions or intermediate_solutions or nr_solutions is not None
        )
        solution: Union[Optional[Any], List[Any]] = (
            [] if multiple_solutions else None
        )

        async for result in self.solutions(
            time_limit=time_limit,
            nr_solutions=nr_solutions,
            processes=processes,
            random_seed=random_seed,
            all_solutions=all_solutions,
            intermediate_solutions=intermediate_solutions,
            free_search=free_search,
            optimisation_level=optimisation_level,
            timeout=timeout,
            **kwargs,
        ):
            status = result.status
            statistics.update(result.statistics)
            if result.solution is not None:
                if multiple_solutions:
                    assert isinstance(solution, list)
                    solution.append(result.solution)
                else:
                    solution = result.solution
        return Result(status, solution, statistics)

    async def diverse_solutions(
        self,
        num_diverse_solutions: Optional[int] = None,
        reference_solution: Optional[Union[Result, Dict]] = None,
        mzn_analyse: Optional[MznAnalyse] = None,
        optimise_diverse_sol: Optional[bool] = True,
        solver: Optional[Solver] = None,
    ) -> AsyncIterator[Result]:
        """Solves the Instance to find diverse solutions using its given solver configuration.

        Finds diverse solutions to the given MiniZinc instance using the given solver
        configuration. Every diverse solution is yielded one at a
        time. If a reference solution is provided the diverse solutions are generated
        around it. For more information regarding this methods and its
        arguments, see the documentation of :func:`~MiniZinc.Instance.diverse_solutions`.

        Yields:
            Result: (TODO)
                A Result object containing the current solving status, values
                assigned, and statistical information.

        """
        from .helpers import (
            _add_diversity_to_div_model,
            _add_diversity_to_opt_model,
        )

        # Loads diverse solution generator if MiniZinc Data Annotator is present
        if mzn_analyse is None:
            mzn_analyse = MznAnalyse.find()
        if mzn_analyse is None:
            raise ConfigurationError(
                "mzn-analyse executable could not be located"
            )

        # Create a temporary file in which the diversity model (generated by mzn-analyse) is placed
        div_file = tempfile.NamedTemporaryFile(
            prefix="mzn_div", suffix=".mzn", delete=False
        )

        try:
            # Extract the diversity annotations.
            with self.files() as files:
                div_anns = mzn_analyse.run(
                    files,
                    get_diversity_anns=True,
                    inline_includes=InlineOption.NON_LIBRARY,
                    remove_items=["output"],
                    remove_anns=["mzn_expression_name"],
                    remove_litter=True,
                    mzn_output=Path(div_file.name),
                )["get-diversity-annotations"]

            # Objective annotations.
            obj_anns = div_anns["objective"]
            variables = div_anns["vars"]

            if len(variables) <= 0:
                raise MiniZincError(message="No distance measure is specified")

            if solver is None:
                solver = self._solver
            inst = Instance(solver, Model(Path(div_file.name)), self._driver)

            max_gap = None  # Place holder for max gap.
            prev_solutions = None  # Place holder for prev solutions

            # Number of total diverse solutions - If not provided use the count provided in the MiniZinc model
            div_num = (
                int(div_anns["k"])
                if num_diverse_solutions is None
                else num_diverse_solutions
            )
            # Increase the solution count by one if a reference solution is provided
            if reference_solution:
                div_num += 1

            # Initial (re-)optimisation run
            with inst.branch() as child:
                # Add constraints to the model that sets the decision variables to the reference solution, if provided
                if reference_solution:
                    if (
                        isinstance(reference_solution, Result)
                        and is_dataclass(reference_solution.solution)
                        and not isinstance(reference_solution.solution, type)
                    ):
                        solution_obj = asdict(reference_solution.solution)
                    else:
                        assert isinstance(reference_solution, dict)
                        solution_obj = reference_solution
                    for k, v in solution_obj.items():
                        if k not in ("objective", "_output_item", "_checker"):
                            child[k] = v

                # We will extend the annotated model with the objective and vars.
                child = _add_diversity_to_opt_model(child, obj_anns, variables)

                # Solve original model to optimality.
                if minizinc.logger.isEnabledFor(logging.INFO):
                    model_type = "opt" if obj_anns["sense"] != "0" else "sat"
                    minizinc.logger.info(
                        f"[Sol 1] Solving the original ({model_type}) model to get a solution"
                    )
                res: Result = await child.solve_async()
                # No (additional) solutions can be found, return from function
                if res.solution is None:
                    return

            if reference_solution is None:
                yield res

            # Calculate max gap.
            max_gap = (
                (1 - int(obj_anns["sense"]) * float(div_anns["gap"]))
                * float(res["div_orig_opt_objective"])
                if obj_anns["sense"] != "0"
                else 0
            )

            # Store current solution as previous solution
            prev_solutions = asdict(res.solution)

            for i in range(2, div_num + 1):
                with inst.branch() as child:
                    minizinc.logger.info(
                        f"[Sol {i}] Generating diverse solution {i}"
                        + (" (optimal)" if optimise_diverse_sol else "")
                    )

                    # We will extend the annotated model with the objective and vars.
                    child = _add_diversity_to_div_model(
                        child,
                        variables,
                        div_anns,
                        max_gap,
                        prev_solutions,
                    )

                    # Solve div model to get a diverse solution.
                    res = await child.solve_async()

                # No (additional) solutions can be found, return from function
                if res.solution is None:
                    return

                # Solve diverse solution to optimality after fixing the diversity vars to the obtained solution
                if optimise_diverse_sol:
                    # Solution as dictionary
                    sol_div = asdict(res.solution)

                    # COMMENDTED OUT FOR NOW: Merge the solution values.
                    # sol_dist = dict()
                    # for var in variables:
                    #     distvarname = "dist_"+var["name"]
                    #     sol_dist[distvarname] = (sol_div[distvarname])

                    # Solve opt model after fixing the diversity vars to the obtained solution
                    with inst.branch() as child:
                        child = _add_diversity_to_opt_model(
                            child, obj_anns, variables, sol_div
                        )

                        # Solve the model
                        res = await child.solve_async()

                        # No (additional) solutions can be found, return from function
                        if res.solution is None:
                            return

                    # COMMENDTED OUT FOR NOW: Add distance to previous solutions
                    # sol_opt = asdict(res.solution)
                    # sol_opt["distance_to_prev_vars"] = sol_dist
                yield res

                # Store current solution as previous solution
                curr_solution = asdict(res.solution)
                # Add the current solution to prev solution container
                assert prev_solutions is not None
                for var in variables:
                    prev_solutions[var["prev_name"]].append(
                        curr_solution[var["name"]]
                    )
        finally:
            # Remove temporary file created for the diversity model
            div_file.close()
            os.remove(div_file.name)

    async def solutions(
        self,
        time_limit: Optional[timedelta] = None,
        nr_solutions: Optional[int] = None,
        processes: Optional[int] = None,
        random_seed: Optional[int] = None,
        all_solutions: bool = False,
        intermediate_solutions: Optional[bool] = None,
        free_search: bool = False,
        optimisation_level: Optional[int] = None,
        verbose: bool = False,
        debug_output: Optional[Path] = None,
        timeout: Optional[timedelta] = None,
        **kwargs,
    ) -> AsyncIterator[Result]:
        """An asynchronous generator for solutions of the MiniZinc instance.

        This method provides an asynchronous generator for the solutions of the
        MiniZinc instance. Every (intermediate) solution is yielded one at a
        time, the last item yielded from the generator will not contain a new
        solution, but will return the final Status and all remaining
        statistical values. For more information regarding this methods and its
        arguments, see the documentation of :func:`~MiniZinc.Instance.solve`.

        Yields:
            Result:
                A Result object containing the current solving status, values
                assigned, and statistical information.

        """
        # rewrite deprecated option `timeout`
        if timeout is not None and time_limit is None:
            warnings.warn(
                "The usage of the `timeout` parameter is deprecated, please use the `time_limit` parameter instead.",
                DeprecationWarning,
                stacklevel=1,
            )
            time_limit = timeout

        method = self.method  # Ensure self.analyse() has been executed
        # Set standard command line arguments
        cmd: List[Union[str, Path]] = [
            "--output-mode",
            "json",  # Ensure MiniZinc's solutions are given as parsable JSON
            "--output-time",  # Output MiniZinc recorded time with every solution
            "--output-objective",  # Output objective value with every solution
            "--statistics",  # Enable statistics
        ]
        # Add the model's evaluated output item to the json output object
        if self.has_output_item:
            cmd.append("--output-output-item")

        # Process number of solutions to be generated
        if all_solutions:
            if nr_solutions is not None:
                raise ValueError(
                    "The number of solutions cannot be limited when looking "
                    "for all solutions"
                )
            if method == Method.SATISFY:
                if "-a" not in self._solver.stdFlags:
                    raise NotImplementedError(
                        "Solver does not support the -a flag"
                    )
                cmd.append("--all-solutions")
            else:
                if "-a-o" not in self._solver.stdFlags:
                    raise NotImplementedError(
                        "Solver does not support the -a-o flag"
                    )
                cmd.append("--all-optimal")
        elif nr_solutions is not None:
            if nr_solutions <= 0:
                raise ValueError(
                    "The number of solutions can only be set to a positive "
                    "integer number"
                )
            if self.method == Method.SATISFY:
                if "-n" not in self._solver.stdFlags:
                    raise NotImplementedError(
                        "Solver does not support the -n flag"
                    )
                cmd.extend(["--num-solutions", str(nr_solutions)])
            else:
                if "-n-o" not in self._solver.stdFlags:
                    raise NotImplementedError(
                        "Solver does not support the -n-o flag"
                    )
                cmd.extend(["--num-optimal", str(nr_solutions)])
        elif intermediate_solutions:
            if (
                "-i" not in self._solver.stdFlags
                and "-a" not in self._solver.stdFlags
            ):
                raise NotImplementedError(
                    "Solver does not support the -i and -a flags"
                )
            cmd.append("--intermediate-solutions")
        elif (intermediate_solutions is None and time_limit is not None) and (
            "-i" in self._solver.stdFlags or "-a" in self._solver.stdFlags
        ):
            # Enable intermediate solutions just in case to ensure that there is
            # a best solution available at the time limit.
            cmd.append("--intermediate-solutions")
        # Set number of processes to be used
        if processes is not None:
            cmd.extend(["--parallel", str(processes)])
        # Set random seed to be used
        if random_seed is not None:
            cmd.extend(["--random-seed", str(random_seed)])
        # Enable free search if specified
        if free_search:
            cmd.append("--free-search")
        # Set compiler optimisation level if specified
        if optimisation_level is not None:
            cmd.extend(["-O", str(optimisation_level)])

        # Set time limit for the MiniZinc solving
        if time_limit is not None:
            cmd.extend(
                ["--time-limit", str(int(time_limit.total_seconds() * 1000))]
            )

        if verbose:
            cmd.append("--verbose")

        for flag, value in kwargs.items():
            if not flag.startswith("-"):
                flag = "--" + flag
            if isinstance(value, bool):
                if value:
                    cmd.append(flag)
            else:
                cmd.extend([flag, value])

        multiple_solutions = (
            all_solutions
            or intermediate_solutions
            or (nr_solutions is not None)
        )

        # Add files as last arguments
        with self.files() as files, self._solver.configuration() as solver:
            assert self.output_type is not None
            cmd.extend(files)

            status = Status.UNKNOWN
            code = 0
            solution = None
            statistics: Dict[str, Any] = {}

            # Whether the status has changed since the last `yield`
            status_changed = False

            # Run the MiniZinc process
            proc = await self._driver._create_process(cmd, solver=solver)
            assert isinstance(proc.stderr, asyncio.StreamReader)
            assert isinstance(proc.stdout, asyncio.StreamReader)
            read_stderr = asyncio.create_task(_read_all(proc.stderr))

            try:
                async for obj in decode_async_json_stream(
                    proc.stdout, cls=MZNJSONDecoder, enum_map=self._enum_map
                ):
                    new_solution, new_status, statistics = (
                        self._parse_stream_obj(obj, statistics)
                    )
                    if new_status is not None:
                        status = new_status
                        status_changed = True
                    elif new_solution is not None:
                        solution = new_solution
                        if status == Status.UNKNOWN:
                            status = Status.SATISFIED
                        if multiple_solutions:
                            yield Result(status, solution, statistics)
                            solution = None
                            statistics = {}
                            status_changed = False

                code = await proc.wait()
            except asyncio.IncompleteReadError as err:
                # End of Stream has been reached
                # Read remaining text in buffer
                code = await proc.wait()
                remainder = err.partial.strip()

                # Parse and output the remaining statistics and status messages
                if remainder != b"":
                    try:
                        obj = json.loads(
                            remainder,
                            cls=MZNJSONDecoder,
                            enum_map=self._enum_map,
                        )
                    except json.JSONDecodeError as e:
                        raise MiniZincError(
                            message=f"MiniZinc driver output a message that cannot be parsed as JSON:\n{repr(remainder)}"
                        ) from e
                    new_solution, new_status, statistics = (
                        self._parse_stream_obj(obj, statistics)
                    )
                    if new_status is not None:
                        status = new_status
                        status_changed = True
                    elif new_solution is not None:
                        solution = new_solution
                        if status == Status.UNKNOWN:
                            status = Status.SATISFIED
                        if multiple_solutions:
                            yield Result(status, solution, statistics)
                            solution = None
                            statistics = {}
                            status_changed = False

            except (asyncio.CancelledError, MiniZincError, Exception):
                # Process was cancelled by the user, a MiniZincError occurred, or
                # an unexpected Python exception occurred
                # First, terminate the process
                if sys.platform == "win32":
                    with open(
                        f"\\\\.\\pipe\\minizinc-{proc.pid}", mode="w"
                    ) as named_pipe:
                        # Trigger MiniZinc termination
                        named_pipe.write("")
                else:
                    proc.terminate()
                _ = await proc.wait()
                # Then, reraise the error that occurred
                raise

            if not multiple_solutions:
                yield Result(status, solution, statistics)
            elif status_changed or statistics != {}:
                yield Result(status, None, statistics)

            # Raise error if required
            stderr = await read_stderr
            if code != 0 or status == Status.ERROR:
                raise parse_error(stderr)

            if debug_output is not None:
                debug_output.write_bytes(stderr)

    @contextlib.contextmanager
    def branch(self) -> Iterator["Instance"]:  # TODO: Self reference
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
        child = self.__class__(self._solver)
        child._parent = self

        # Copy current information from analysis
        child._method_cache = self.method
        child.output_type = self.output_type
        child._output_cache = self._output_cache
        child._input_cache = self._input_cache

        with self._lock:
            yield child

    @contextlib.contextmanager
    def files(self) -> Iterator[List[Path]]:
        """Gets list of files of the Instance

        Files will create a list of paths to the files that together form the
        Instance. Parts of the Instance might be saved to files and are only
        guaranteed to exist while within the created context.

        Yields:
            List of Path objects to existing and created files
        """

        files: List[Path] = []
        fragments: List[str] = []
        data: Dict[str, Any] = {}

        inst: Optional["Instance"] = self
        while inst is not None:
            for k, v in inst._data.items():
                if isinstance(v, UnknownExpression) or k in data:
                    fragments.append(f"{k} = {v};\n")
                elif isinstance(v, EnumMeta):
                    data[k] = [str(mem) for mem in v.__members__]
                else:
                    data[k] = v
            fragments.extend(inst._code_fragments)
            files.extend(inst._includes)

            inst = inst._parent

        gen_files = []
        try:
            if len(data) > 0:
                file = tempfile.NamedTemporaryFile(
                    prefix="mzn_data", suffix=".json", delete=False
                )
                gen_files.append(file)
                file.write(
                    json.dumps(
                        data, cls=MZNJSONEncoder, ensure_ascii=False
                    ).encode()
                )
                file.close()
                files.append(Path(file.name))
            if len(fragments) > 0 or len(files) == 0:
                file = tempfile.NamedTemporaryFile(
                    prefix="mzn_fragment", suffix=".mzn", delete=False
                )
                gen_files.append(file)
                for code in fragments:
                    file.write(code.encode())
                file.close()
                files.append(Path(file.name))
            yield files
        finally:
            for file in gen_files:
                file.close()
                os.remove(file.name)

    @property
    def method(self) -> Method:
        """Query the Method used by the Instance.

        Returns:
            Method: Method of the goal used by the Instance.
        """
        if self._method_cache is None:
            self.analyse()
        assert self._method_cache is not None
        return self._method_cache

    @property
    def input(self) -> Dict[str, Type]:
        """Query the input parameters of the Instance.

        Returns:
            Dict[str, Type]: A mapping from parameter identifiers to their Types.
        """
        if self._input_cache is None or self._method_cache is None:
            self.analyse()
        assert self._input_cache is not None
        return self._input_cache

    @property
    def output(self):
        """Query the output parameters of the Instance.

        Returns:
            Dict[str, Type]: A mapping from parameter identifiers to their Types.
        """
        if self._output_cache is None or self._method_cache is None:
            self.analyse()
        assert self._output_cache is not None
        return self._output_cache

    @property
    def has_output_item(self) -> bool:
        """Query whether the instance constains an output item.

        Returns:
            bool: whether the instance contains an output item.
        """
        if self._has_output_item_cache is None:
            self.analyse()
        assert self._has_output_item_cache is not None
        return self._has_output_item_cache

    def analyse(self):
        """Discovers basic information about a CLIInstance

        Analyses a given instance and discovers basic information about set
        model such as the solving method, the input parameters, and the output
        parameters. The information found will be stored among the attributes
        of the instance.
        """
        with self.files() as files:
            assert len(files) > 0
            output = self._driver._run(
                ["--model-interface-only"] + files, self._solver
            )
        interface = None
        for obj in decode_json_stream(output.stdout):
            if obj["type"] == "interface":
                interface = obj
                break
        assert interface is not None
        old_method = self._method_cache
        self._method_cache = Method.from_string(interface["method"])
        self._input_cache = {}
        for key, value in interface["input"].items():
            self._input_cache[key] = _to_python_type(value)
        old_output = self._output_cache
        self._output_cache = {}
        for key, value in interface["output"].items():
            self._output_cache[key] = _to_python_type(value)
        self._has_output_item_cache = interface.get("has_output_item", True)
        if self._has_output_item_cache:
            self._output_cache["_output_item"] = str
        if self._checker:
            self._output_cache["_checker"] = str

        if self.output_type is None or (
            issubclass(self.output_type, _GeneratedSolution)
            and (
                self._output_cache != old_output
                or self._method_cache != old_method
            )
        ):
            fields = []
            self._field_renames = []
            if (
                self._method_cache is not Method.SATISFY
                and "objective" not in self._output_cache
            ):
                fields.append(("objective", Number))
            for k, v in self._output_cache.items():
                if k in ["_output_item", "_checker"]:
                    fields.append((k, str, field(default="")))
                elif iskeyword(k):
                    warnings.warn(
                        f"MiniZinc field '{k}' is a Python keyword. It has been "
                        f"renamed to 'mzn_{k}'",
                        SyntaxWarning,
                        stacklevel=1,
                    )
                    self._field_renames.append((k, "mzn_" + k))
                    fields.append(("mzn_" + k, v))
                else:
                    fields.append((k, v))

            minizinc.logger.debug(
                f"CLIInstance:analyse -> output fields: "
                f"{[f[0:2] for f in fields]}"
            )

            methods = {}
            if self._has_output_item_cache:
                methods["__str__"] = lambda myself: (
                    myself.__repr__()
                    if myself._output_item == ""
                    else myself._output_item
                )
            if self._checker:
                methods["check"] = lambda myself: myself._checker

            self.output_type = make_dataclass(
                "Solution",
                fields,
                bases=(_GeneratedSolution,),
                namespace=methods,
                frozen=True,
            )

    def _reset_analysis(self):
        self._method_cache = None

    @contextlib.contextmanager
    def flat(
        self,
        time_limit: Optional[timedelta] = None,
        optimisation_level: Optional[int] = None,
        timeout: Optional[timedelta] = None,
        **kwargs,
    ):
        """Produce a FlatZinc file for the instance.

        Args:
            time_limit (Optional[timedelta]): Set the time limit for the process
                of flattening the instance. TODO: An exception is raised if the
                timeout is reached.
            optimisation_level (Optional[int]): Set the MiniZinc compiler
                optimisation level.

                - 0: Disable optimisation
                - 1: Single pass optimisation (default)
                - 2: Flatten twice to improve flattening decisions
                - 3: Perform root-node-propagation
                - 4: Probe bounds of all variables at the root node
                - 5: Probe values of all variables at the root node

            **kwargs: Other flags to be passed to the compiler. ``--`` can be
                omitted in the name of the flag. If the type of the flag is
                Boolean, then its value signifies its occurrence.

        Yields:
            Tuple containing the files of the FlatZinc model, the output model
            and a dictionary the statistics of flattening

        """
        # rewrite deprecated option `timeout`
        if timeout is not None and time_limit is None:
            warnings.warn(
                "The usage of the `timeout` parameter is deprecated, please use the `time_limit` parameter instead.",
                DeprecationWarning,
                stacklevel=1,
            )
            time_limit = timeout

        cmd: List[Any] = ["--compile", "--statistics"]

        fzn = tempfile.NamedTemporaryFile(
            prefix="fzn_", suffix=".fzn", delete=False
        )
        cmd.extend(["--fzn", fzn.name])
        fzn.close()
        ozn = tempfile.NamedTemporaryFile(
            prefix="ozn_", suffix=".fzn", delete=False
        )
        cmd.extend(["--ozn", ozn.name])
        ozn.close()

        if time_limit is not None:
            cmd.extend(
                ["--time-limit", str(int(time_limit.total_seconds() * 1000))]
            )

        # Set compiler optimisation level if specified
        if optimisation_level is not None:
            cmd.extend(["-O", str(optimisation_level)])

        for flag, value in kwargs.items():
            if not flag.startswith("-"):
                flag = f"--{flag}"
            if isinstance(value, bool):
                if value:
                    cmd.append(flag)
            else:
                cmd.extend([flag, value])

        # Add files as last arguments
        with self.files() as files:
            cmd.extend(files)
            # Run the MiniZinc process
            output = self._driver._run(cmd, solver=self._solver)

        statistics: Dict[str, Any] = {}
        matches = re.findall(rb"%%%mzn-stat:? (\w*)=([^\r\n]*)", output.stdout)
        for m in matches:
            set_stat(statistics, m[0].decode(), m[1].decode())

        try:
            yield fzn, ozn, statistics
        finally:
            os.remove(fzn.name)
            os.remove(ozn.name)

    def add_file(self, file: ParPath, parse_data: bool = True) -> None:
        self._reset_analysis()
        return super().add_file(file, parse_data)

    def add_string(self, code: str) -> None:
        self._reset_analysis()
        return super().add_string(code)

    def _parse_stream_obj(self, obj, statistics):
        solution = None
        status = None
        if obj["type"] == "solution":
            tmp = obj["output"]["json"]
            if "_objective" in tmp:
                tmp["objective"] = tmp.pop("_objective")
            if "_output" in tmp:
                tmp["_output_item"] = tmp.pop("_output")
            for before, after in self._field_renames:
                tmp[after] = tmp.pop(before)

            if "_checker" in statistics:
                tmp["_checker"] = statistics.pop("_checker")

            assert self.output_type is not None
            solution = self.output_type(**tmp)
            statistics["time"] = timedelta(milliseconds=obj["time"])
        elif obj["type"] == "time":
            statistics["time"] = timedelta(milliseconds=obj["time"])
        elif obj["type"] == "statistics":
            for key, val in obj["statistics"].items():
                set_stat(statistics, key, str(val))
        elif obj["type"] == "status":
            status = Status.from_str(obj["status"])
        elif obj["type"] == "checker":
            if "raw" in obj["output"]:
                statistics["_checker"] = obj["output"]["raw"]
            else:
                # TODO: can we ensure this is made JSON?
                statistics["_checker"] = obj["output"]["dzn"]

        return solution, status, statistics


def _to_python_type(mzn_type: dict) -> Type:
    """Converts MiniZinc JSON type to Type

    Converts a MiniZinc JSON type definition generated by the MiniZinc CLI to a
    Python Type object. This can be used on types that result from calling
    ``minizinc --model-interface-only``.

    Args:
        mzn_type (dict): MiniZinc type definition as resulting from JSON

    Returns:
        Type: Type definition in Python

    """
    basetype = mzn_type["type"]
    pytype: Type
    # TODO: MiniZinc does not report enumerated types correctly
    if basetype == "bool":
        pytype = bool
    elif basetype == "float":
        pytype = float
    elif basetype == "int":
        pytype = int
    elif basetype == "string":
        pytype = str
    elif basetype == "ann":
        pytype = str
    elif basetype == "tuple":
        pytype = list
    elif basetype == "record":
        pytype = dict
    else:
        warnings.warn(
            f"Unable to determine minizinc type `{basetype}` assuming integer type",
            FutureWarning,
            stacklevel=1,
        )
        pytype = int

    if mzn_type.get("set", False):
        if pytype is int:
            pytype = Union[Set[int], range]  # type: ignore
        else:
            pytype = Set[pytype]  # type: ignore

    dim = mzn_type.get("dim", 0)
    while dim >= 1:
        # No typing support for n-dimensional typing
        pytype = List[pytype]  # type: ignore
        dim -= 1
    return pytype


async def _read_all(stream: asyncio.StreamReader):
    output: bytes = b""
    while not stream.at_eof():
        try:
            output += await stream.read()
            return output
        except asyncio.LimitOverrunError as err:
            output += await stream.readexactly(err.consumed)
    return output
