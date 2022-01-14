#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at http://mozilla.org/MPL/2.0/.

import asyncio
import contextlib
import json
import os
import re
import sys
import tempfile
import warnings
from dataclasses import field, make_dataclass
from datetime import timedelta
from enum import EnumMeta
from keyword import iskeyword
from numbers import Number
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Tuple, Type, cast

import minizinc
from minizinc.error import MiniZincError, parse_error
from minizinc.instance import Instance
from minizinc.json import (
    MZNJSONDecoder,
    MZNJSONEncoder,
    decode_async_json_stream,
    decode_json_stream,
)
from minizinc.model import Method, Model, ParPath, UnknownExpression
from minizinc.result import Result, Status, parse_solution, set_stat
from minizinc.solver import Solver

from .driver import CLIDriver, to_python_type

if sys.version_info >= (3, 8):
    from typing import Final

    SEPARATOR: Final[bytes] = str.encode("----------" + os.linesep)
else:
    SEPARATOR: bytes = str.encode("----------" + os.linesep)


class _GeneratedSolution:
    pass


class CLIInstance(Instance):
    _driver: CLIDriver
    _solver: Solver
    _input: Optional[Dict[str, Type]] = None
    _output: Optional[Dict[str, Type]] = None
    _method: Optional[Method] = None
    _parent: Optional["CLIInstance"] = None
    _field_renames: List[Tuple[str, str]]

    def __init__(
        self,
        solver: Solver,
        model: Optional[Model] = None,
        driver: Optional[CLIDriver] = None,
    ):
        super().__init__(solver, model)
        self._solver = solver
        self._field_renames = []
        if driver is not None:
            self._driver = driver
        elif minizinc.default_driver is not None and isinstance(
            minizinc.default_driver, CLIDriver
        ):
            self._driver = cast(CLIDriver, minizinc.default_driver)
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

    @contextlib.contextmanager
    def branch(self) -> Iterator[Instance]:  # TODO: Self reference
        child = self.__class__(self._solver)
        child._parent = self

        # Copy current information from analysis
        child._method = self.method
        child.output_type = self.output_type
        child._output = self._output
        child._input = self.input

        with self._lock:
            yield child

    @property
    def method(self) -> Method:
        if self._method is None:
            self.analyse()
        assert self._method is not None
        return self._method

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

        inst: Optional["CLIInstance"] = self
        while inst is not None:
            for k, v in inst._data.items():
                if isinstance(v, UnknownExpression) or k in data:
                    fragments.append(f"{k} = {v};\n")
                elif isinstance(v, EnumMeta):
                    fragments.append(
                        f"{k} = {{{', '.join([i for i in v.__members__])}}};\n"
                    )
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
                file.write(json.dumps(data, cls=MZNJSONEncoder).encode())
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
    def input(self):
        if self._input is None or self._method is None:
            self.analyse()
        return self._input

    @property
    def output(self):
        if self._output is None or self._method is None:
            self.analyse()
        return self._output

    def analyse(self):
        """Discovers basic information about a CLIInstance

        Analyses a given instance and discovers basic information about set
        model such as the solving method, the input parameters, and the output
        parameters. The information found will be stored among the attributes
        of the instance.
        """
        with self.files() as files:
            assert len(files) > 0
            output = self._driver.run(["--model-interface-only"] + files, self._solver)
        if self._driver.parsed_version >= (2, 6, 0):
            interface = None
            for obj in decode_json_stream(output.stdout):
                if obj["type"] == "interface":
                    interface = obj
                    break
        else:
            interface = json.loads(output.stdout)
        old_method = self._method
        self._method = Method.from_string(interface["method"])
        self._input = {}
        for key, value in interface["input"].items():
            self._input[key] = to_python_type(value)
        old_output = self._output
        self._output = {}
        for (key, value) in interface["output"].items():
            self._output[key] = to_python_type(value)
        if interface.get("has_output_item", True):
            self._output["_output_item"] = str
        if self._checker:
            self._output["_checker"] = str

        if self.output_type is None or (
            issubclass(self.output_type, _GeneratedSolution)
            and (self._output != old_output or self._method != old_method)
        ):
            fields = []
            self._field_renames = []
            if self._method is not Method.SATISFY and "objective" not in self._output:
                fields.append(("objective", Number))
            for k, v in self._output.items():
                if k in ["_output_item", "_checker"]:
                    fields.append((k, str, field(default="")))
                elif iskeyword(k):
                    warnings.warn(
                        f"MiniZinc field '{k}' is a Python keyword. It has been "
                        f"renamed to 'mzn_{k}'",
                        SyntaxWarning,
                    )
                    self._field_renames.append((k, "mzn_" + k))
                    fields.append(("mzn_" + k, v))
                else:
                    fields.append((k, v))

            minizinc.logger.debug(
                f"CLIInstance:analyse -> output fields: " f"{[f[0:2] for f in fields]}"
            )

            methods = {}
            if interface.get("has_output_item", True):
                methods["__str__"] = (
                    lambda myself: myself.__repr__()
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
        self._method = None

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
        verbose: bool = False,
        debug_output: Optional[Path] = None,
        **kwargs,
    ):
        method = self.method  # Ensure self.analyse() has been executed
        # Set standard command line arguments
        cmd: List[Any] = [
            "--output-mode",
            "json",
            "--output-time",
            "--output-objective",
            "--output-output-item",
            "--statistics",  # Enable statistics
            # Enable intermediate solutions
            # (ensure that solvers always output their best solution)
            "--intermediate-solutions",
        ]

        # Process number of solutions to be generated
        if all_solutions:
            if nr_solutions is not None:
                raise ValueError(
                    "The number of solutions cannot be limited when looking "
                    "for all solutions"
                )
            if method != Method.SATISFY:
                raise NotImplementedError(
                    "Finding all optimal solutions is not yet implemented"
                )
            if "-a" not in self._solver.stdFlags:
                raise NotImplementedError("Solver does not support the -a flag")
            cmd.append("--all-solutions")
        elif nr_solutions is not None:
            if nr_solutions <= 0:
                raise ValueError(
                    "The number of solutions can only be set to a positive "
                    "integer number"
                )
            if self.method != Method.SATISFY:
                raise NotImplementedError(
                    "Finding multiple optimal solutions is not yet implemented"
                )
            if "-n" not in self._solver.stdFlags:
                raise NotImplementedError("Solver does not support the -n flag")
            cmd.extend(["--num-solutions", str(nr_solutions)])
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
        if timeout is not None:
            cmd.extend(["--time-limit", str(int(timeout.total_seconds() * 1000))])

        if verbose:
            cmd.append("--verbose")

        for flag, value in kwargs.items():
            if not flag.startswith("-"):
                flag = "--" + flag
            if type(value) is bool:
                if value:
                    cmd.append(flag)
            else:
                cmd.extend([flag, value])

        # Add files as last arguments
        with self.files() as files, self._solver.configuration() as solver:
            assert self.output_type is not None
            cmd.extend(files)

            status = Status.UNKNOWN
            last_status = Status.UNKNOWN
            code = 0
            statistics: Dict[str, Any] = {}

            try:
                # Run the MiniZinc process
                proc = await self._driver.create_process(cmd, solver=solver)
                assert isinstance(proc.stderr, asyncio.StreamReader)
                assert isinstance(proc.stdout, asyncio.StreamReader)

                # Python 3.7+: replace with asyncio.create_task
                read_stderr = asyncio.ensure_future(_read_all(proc.stderr))

                if self._driver.parsed_version >= (2, 6, 0):
                    async for obj in decode_async_json_stream(
                        proc.stdout, cls=MZNJSONDecoder, enum_map=self._enum_map
                    ):
                        solution, new_status, statistics = self._parse_stream_obj(
                            obj, statistics
                        )
                        if new_status is not None:
                            status = new_status
                        elif solution is not None:
                            if status == Status.UNKNOWN:
                                status = Status.SATISFIED
                            yield Result(status, solution, statistics)
                            last_status = status
                            solution = None
                            statistics = {}
                else:
                    async for raw_sol in _seperate_solutions(proc.stdout):
                        status = Status.SATISFIED
                        solution, statistics = parse_solution(
                            raw_sol,
                            self.output_type,
                            self._enum_map,
                            self._field_renames,
                        )
                        yield Result(Status.SATISFIED, solution, statistics)

                code = await proc.wait()
            except asyncio.IncompleteReadError as err:
                # End of Stream has been reached
                # Read remaining text in buffer
                code = await proc.wait()
                remainder = err.partial

                # Parse and output the remaining statistics and status messages
                if self._driver.parsed_version >= (2, 6, 0):
                    for obj in decode_json_stream(
                        remainder, cls=MZNJSONDecoder, enum_map=self._enum_map
                    ):
                        solution, new_status, statistics = self._parse_stream_obj(
                            obj, statistics
                        )
                        if new_status is not None:
                            status = new_status
                        elif solution is not None:
                            if status == Status.UNKNOWN:
                                status = Status.SATISFIED
                            yield Result(status, solution, statistics)
                            solution = None
                            statistics = {}
                else:
                    for res in filter(None, remainder.split(SEPARATOR)):
                        new_status = Status.from_output(res, method)
                        if new_status is not None:
                            status = new_status
                        solution, statistics = parse_solution(
                            res,
                            self.output_type,
                            self._enum_map,
                            self._field_renames,
                        )
                        yield Result(status, solution, statistics)
            except (asyncio.CancelledError, MiniZincError, Exception):
                # Process was cancelled by the user, a MiniZincError occurred, or
                # an unexpected Python exception occurred
                # First, terminate the process
                proc.terminate()
                _ = await proc.wait()
                # Then, reraise the error that occurred
                raise
            if self._driver.parsed_version >= (2, 6, 0) and (
                status != last_status or statistics != {}
            ):
                yield Result(status, None, statistics)

            # Raise error if required
            stderr = await read_stderr
            if code != 0 or status == Status.ERROR:
                raise parse_error(stderr)

            if debug_output is not None:
                debug_output.write_bytes(stderr)

    @contextlib.contextmanager
    def flat(
        self,
        timeout: Optional[timedelta] = None,
        optimisation_level: Optional[int] = None,
        **kwargs,
    ):
        """Produce a FlatZinc file for the instance.

        Args:
            timeout (Optional[timedelta]): Set the time limit for the process
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
        cmd: List[Any] = ["--compile", "--statistics"]

        fzn = tempfile.NamedTemporaryFile(prefix="fzn_", suffix=".fzn", delete=False)
        cmd.extend(["--fzn", fzn.name])
        fzn.close()
        ozn = tempfile.NamedTemporaryFile(prefix="ozn_", suffix=".fzn", delete=False)
        cmd.extend(["--ozn", ozn.name])
        ozn.close()

        if timeout is not None:
            cmd.extend(["--time-limit", str(int(timeout.total_seconds() * 1000))])

        # Set compiler optimisation level if specified
        if optimisation_level is not None:
            cmd.extend(["-O", str(optimisation_level)])

        for flag, value in kwargs.items():
            if not flag.startswith("-"):
                flag = "--" + flag
            if type(value) is bool:
                if value:
                    cmd.append(flag)
            else:
                cmd.extend([flag, value])

        # Add files as last arguments
        with self.files() as files:
            cmd.extend(files)
            # Run the MiniZinc process
            output = self._driver.run(cmd, solver=self._solver)

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

            solution = self.output_type(**tmp)
            statistics["time"] = obj["time"]
        elif obj["type"] == "time":
            statistics["time"] = obj["time"]
        elif obj["type"] == "statistics":
            statistics.update(obj["statistics"])
        elif obj["type"] == "status":
            status = Status.from_str(obj["status"])
        elif obj["type"] == "checker":
            if "raw" in obj["output"]:
                statistics["_checker"] = obj["output"]["raw"]
            else:
                # TODO: can we ensure this is made JSON?
                statistics["_checker"] = obj["output"]["dzn"]

        return solution, status, statistics


async def _seperate_solutions(stream: asyncio.StreamReader):
    solution: bytes = b""
    while not stream.at_eof():
        try:
            solution += await stream.readuntil(SEPARATOR)
            yield solution
            solution = b""
        except asyncio.LimitOverrunError as err:
            solution += await stream.readexactly(err.consumed)


async def _read_all(stream: asyncio.StreamReader):
    output: bytes = b""
    while not stream.at_eof():
        try:
            output += await stream.read()
            return output
        except asyncio.LimitOverrunError as err:
            output += await stream.readexactly(err.consumed)
    return output
