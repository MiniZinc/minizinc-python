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
from dataclasses import field, make_dataclass
from datetime import datetime, timedelta
from enum import EnumMeta
from numbers import Number
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Type, cast

import minizinc
from minizinc.dzn import UnknownExpression
from minizinc.error import parse_error
from minizinc.instance import Instance
from minizinc.json import MZNJSONEncoder
from minizinc.model import Method, Model, ParPath
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

    def __init__(
        self,
        solver: Solver,
        model: Optional[Model] = None,
        driver: Optional[CLIDriver] = None,
    ):
        super().__init__(solver, model)
        self._solver = solver
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
        try:
            with self._lock:
                yield child
        finally:
            del child

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
                os.remove(file.name)

    @property
    def input(self):
        if self._input is None or self._method is None:
            self.analyse()
        return self._input

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
        interface = json.loads(
            output.stdout
        )  # TODO: Possibly integrate with the MZNJSONDecoder
        old_method = self._method
        self._method = Method.from_string(interface["method"])
        self._input = {}
        for key, value in interface["input"].items():
            self._input[key] = to_python_type(value)
        old_output = self._output
        self._output = {}
        for (key, value) in interface["output"].items():
            self._output[key] = to_python_type(value)

        if self.output_type is None or (
            issubclass(self.output_type, _GeneratedSolution)
            and (self._output != old_output or self._method != old_method)
        ):
            fields = []
            if self._method is not Method.SATISFY and "objective" not in self._output:
                fields.append(("objective", Number))
            for k, v in self._output.items():
                fields.append((k, v))
            if interface.get("has_output_item", True):
                fields.append(("_output_item", str, field(default="")))

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
        ignore_errors=False,
        **kwargs,
    ):
        # Set standard command line arguments
        cmd: List[Any] = [
            "--output-mode",
            "json",
            "--output-time",
            "--output-objective",
            "--output-output-item",
        ]
        # Enable statistics
        cmd.append("-s")

        # Process number of solutions to be generated
        if all_solutions:
            if nr_solutions is not None:
                raise ValueError(
                    "The number of solutions cannot be limited when looking "
                    "for all solutions"
                )
            if self.method != Method.SATISFY:
                raise NotImplementedError(
                    "Finding all optimal solutions is not yet implemented"
                )
            if "-a" not in self._solver.stdFlags:
                raise NotImplementedError("Solver does not support the -a flag")
            cmd.append("-a")
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
            cmd.extend(["-n", str(nr_solutions)])
        if "-a" in self._solver.stdFlags and self.method != Method.SATISFY:
            cmd.append("-a")
        # Set number of processes to be used
        if processes is not None:
            if "-p" not in self._solver.stdFlags:
                raise NotImplementedError("Solver does not support the -p flag")
            cmd.extend(["-p", str(processes)])
        # Set random seed to be used
        if random_seed is not None:
            if "-r" not in self._solver.stdFlags:
                raise NotImplementedError("Solver does not support the -r flag")
            cmd.extend(["-r", str(random_seed)])
        # Enable free search if specified
        if free_search:
            if "-f" not in self._solver.stdFlags:
                raise NotImplementedError("Solver does not support the -f flag")
            cmd.append("-f")

        # Set time limit for the MiniZinc solving
        if timeout is not None:
            cmd.extend(["--time-limit", str(int(timeout.total_seconds() * 1000))])

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
            assert self.output_type is not None
            cmd.extend(files)
            # Run the MiniZinc process
            proc = await self._driver.create_process(cmd, solver=self._solver)

            status = Status.UNKNOWN
            code = 0
            deadline = None
            if timeout is not None:
                deadline = datetime.now() + timeout + timedelta(seconds=5)

            remainder: Optional[bytes] = None
            try:
                raw_sol: bytes = b""
                while not proc.stdout.at_eof():
                    try:
                        if deadline is None:
                            raw_sol += await proc.stdout.readuntil(SEPARATOR)
                        else:
                            t = deadline - datetime.now()
                            raw_sol += await asyncio.wait_for(
                                proc.stdout.readuntil(SEPARATOR), t.total_seconds()
                            )
                        status = Status.SATISFIED
                        solution, statistics = parse_solution(
                            raw_sol, self.output_type, self._enum_map
                        )
                        yield Result(Status.SATISFIED, solution, statistics)
                        raw_sol = b""
                    except asyncio.LimitOverrunError as err:
                        raw_sol += await proc.stdout.readexactly(err.consumed)

                code = await proc.wait()
            except asyncio.IncompleteReadError as err:
                # End of Stream has been reached
                # Read remaining text in buffer
                code = await proc.wait()
                remainder = err.partial
            except asyncio.TimeoutError:
                # Process was reached hard deadline (timeout + 5 sec)
                # Kill process and read remaining output
                proc.kill()
                await proc.wait()
                remainder = proc.stdout.read()
            finally:
                # parse the remaining statistics
                if remainder is not None:
                    final_status = Status.from_output(remainder, self.method)
                    if final_status is not None:
                        status = final_status
                    solution, statistics = parse_solution(
                        remainder, self.output_type, self._enum_map
                    )
                    yield Result(status, solution, statistics)
                # Raise error if required
                if code != 0 or status == Status.ERROR:
                    stderr = await proc.stderr.read()
                    raise parse_error(stderr)

    async def solve_async(
        self,
        timeout: Optional[timedelta] = None,
        nr_solutions: Optional[int] = None,
        processes: Optional[int] = None,
        random_seed: Optional[int] = None,
        all_solutions=False,
        intermediate_solutions=False,
        free_search: bool = False,
        **kwargs,
    ):
        status = Status.UNKNOWN
        solution = None
        statistics: Dict[str, Any] = {}

        multiple_solutions = (
            all_solutions or intermediate_solutions or nr_solutions is not None
        )
        if multiple_solutions:
            solution = []

        async for result in self.solutions(
            timeout=timeout,
            nr_solutions=nr_solutions,
            processes=processes,
            random_seed=random_seed,
            all_solutions=all_solutions,
            free_search=free_search,
            **kwargs,
        ):
            status = result.status
            statistics.update(result.statistics)
            if result.solution is not None:
                if multiple_solutions:
                    solution.append(result.solution)
                else:
                    solution = result.solution
        return Result(status, solution, statistics)

    @contextlib.contextmanager
    def flat(self, timeout: Optional[timedelta] = None, **kwargs):
        """Produce a FlatZinc file for the instance.

        Args:
            timeout (Optional[timedelta]): Set the time limit for the process
                of flattening the instance. TODO: An exception is raised if the
                timeout is reached.
            **kwargs: Other flags to be passed onto the solver. ``--`` can be
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
            output = self._driver.run(cmd, solver=self._solver, timeout=timeout)

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
