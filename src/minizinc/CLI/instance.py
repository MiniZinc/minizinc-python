#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at http://mozilla.org/MPL/2.0/.

import contextlib
import json
import tempfile
from datetime import timedelta
from pathlib import Path
from typing import Dict, List, Optional, Type

from ..dzn import UnknownExpression
from ..instance import Instance, Method
from ..json import MZNJSONEncoder
from ..model import Model
from ..result import Result
from .driver import to_python_type
from .solver import CLISolver


class CLIInstance(Instance):
    _solver: CLISolver
    _input: Optional[Dict[str, Type]]
    _output: Optional[Dict[str, Type]]
    _method: Optional[Method]
    _parent: Optional[Instance]

    def __init__(self, solver: CLISolver, model: Optional[Model] = None):
        super().__init__(solver, model)
        self._solver = solver
        self._parent = None
        self._method = None
        self._input = None
        self._output = None
        if model is not None:
            self._includes = model._includes.copy()
            self._code_fragments = model._code_fragments.copy()
            self._data = dict.copy(model._data)

    @contextlib.contextmanager
    def branch(self) -> Instance:  # TODO: Self reference
        child = self.__class__(self._solver)
        child._parent = self
        try:
            yield child
        finally:
            del child

    @property
    def method(self) -> Method:
        if self._method is None:
            self.analyse()
        return self._method

    @contextlib.contextmanager
    def files(self) -> List[Path]:
        """Gets list of files of the Instance

        Files will create a list of paths to the files that together form the Instance. Parts of the Instance might be
        saved to files and are only guaranteed to exist while within the created context.

        Yields:
            List of Path objects to existing and created files
        """
        files: List[Path] = self._includes.copy()
        fragments = None
        data = None
        tmp_fragments = self._code_fragments.copy()
        if len(self._data) > 0:
            tmp_data = {}
            for k, v in self._data.items():
                if isinstance(v, UnknownExpression):
                    tmp_fragments.append("%s = %s;\n" % (k, v))
                else:
                    tmp_data[k] = v
            if len(tmp_data) > 0:
                data = tempfile.NamedTemporaryFile(prefix="mzn_data", suffix=".json")
                data.write(json.dumps(tmp_data, cls=MZNJSONEncoder).encode())
                data.flush()
                data.seek(0)
                files.append(Path(data.name))
        if len(tmp_fragments) > 0 or len(files) == 0:
            fragments = tempfile.NamedTemporaryFile(prefix="mzn_fragment", suffix=".mzn")
            for code in tmp_fragments:
                fragments.write(code.encode())
            fragments.flush()
            fragments.seek(0)
            files.append(Path(fragments.name))
        try:
            if self._parent is not None:
                assert isinstance(self._parent, CLIInstance)
                with self._parent.files() as pfiles:
                    yield pfiles + files
            else:
                yield files
        finally:
            if fragments is not None:
                fragments.close()
            if data is not None:
                data.close()

    @property
    def input(self):
        if self._input is None:
            self.analyse()
        return self._input

    def analyse(self):
        """Discovers basic information about a CLIInstance

        Analyses a given instance and discovers basic information about set model such as the solving method, the input
        parameters, and the output parameters. The information found will be stored among the attributes of the
        instance.
        """
        with self.files() as files:
            assert len(files) > 0
            output = self._solver.run(["--model-interface-only"] + files)
        interface = json.loads(output.stdout)  # TODO: Possibly integrate with the MZNJSONDecoder
        self._method = Method.from_string(interface["method"])
        self._input = {}
        for key, value in interface["input"].items():
            self._input[key] = to_python_type(value)
        self._output = {}
        for (key, value) in interface["output"].items():
            self._output[key] = to_python_type(value)

    def solve(self,
              timeout: Optional[timedelta] = None,
              nr_solutions: Optional[int] = None,
              processes: Optional[int] = None,
              random_seed: Optional[int] = None,
              all_solutions=False,
              free_search: bool = False,
              ignore_errors=False,
              **kwargs):
        # Set standard command line arguments
        cmd = ["--output-mode", "json", "--output-time", "--output-objective"]
        # Enable statistics if possible
        if "-s" in self._solver.stdFlags:
            cmd.append("-s")

        # Process number of solutions to be generated
        if all_solutions:
            if nr_solutions is not None:
                raise ValueError("The number of solutions cannot be limited when looking for all solutions")
            if self.method != Method.SATISFY:
                raise NotImplementedError("Finding all optimal solutions is not yet implemented")
            if "-a" not in self._solver.stdFlags:
                raise NotImplementedError("Solver does not support the -a flag")
            cmd.append("-a")
        elif nr_solutions is not None:
            if nr_solutions <= 0:
                raise ValueError("The number of solutions can only be set to a positive integer number")
            if self.method != Method.SATISFY:
                raise NotImplementedError("Finding all optimal solutions is not yet implemented")
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

        # TODO: Should we use --fzn-flags??
        for flag, value in kwargs.items():
            if "--" + flag in [f[0] for f in self._solver.extraFlags]:  # TODO: Check type
                cmd.extend([flag, str(value)])
            else:
                raise NotImplementedError("Solver does not support the --%s flag" % flag)

        # Add files as last arguments
        with self.files() as files:
            cmd.extend(files)
            # Run the MiniZinc process
            output = self._solver.run(cmd)
        return Result.from_process(self, output, ignore_errors)
