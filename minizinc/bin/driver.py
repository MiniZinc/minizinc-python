import json
import re
import subprocess
from pathlib import Path
from typing import Optional

import minizinc.solver
from ..result import Result
from ..driver import Driver
from ..model import Instance, Method


class BinDriver(Driver):

    # Executable path for MiniZinc
    executable: Path

    def __init__(self, executable: Path):
        self.executable = executable

        super(BinDriver, self).__init__(executable)

    def load_solver(self, solver: str) -> minizinc.solver.Solver:
        # Find all available solvers
        output = subprocess.run([self.executable, "--solvers-json"], capture_output=True, check=True)
        solvers = json.loads(output.stdout)

        # Find the specified solver
        info = None
        names = set()
        for s in solvers:
            s_names = [s["id"], s["id"].split(".")[-1]]
            s_names.extend(s.get("tags", []))
            names = names.union(set(s_names))
            if solver in s_names:
                info = s
                break
        if info is None:
            raise LookupError(
                "No solver id or tag '%s' found, available options: %s" % (solver, sorted([x for x in names])))

        # Initialize driver
        ret = minizinc.solver.Solver(info["name"], info["version"], info["executable"], self)

        # Set all specified options
        ret.mznlib = info.get("mznlib", ret.mznlib)
        ret.tags = info.get("tags", ret.mznlib)
        ret.stdFlags = info.get("stdFlags", ret.mznlib)
        ret.extraFlags = info.get("extraFlags", ret.extraFlags)
        ret.supportsMzn = info.get("supportsMzn", ret.mznlib)
        ret.supportsFzn = info.get("supportsFzn", ret.mznlib)
        ret.needsSolns2Out = info.get("needsSolns2Out", ret.mznlib)
        ret.needsMznExecutable = info.get("needsMznExecutable", ret.mznlib)
        ret.needsStdlibDir = info.get("needsStdlibDir", ret.mznlib)
        ret.isGUIApplication = info.get("isGUIApplication", ret.mznlib)
        ret._id = info["id"]

        return ret

    def analyze(self, instance: Instance):
        output = subprocess.run([self.executable, "--model-interface-only"] + instance.files, capture_output=True,
                                check=True)  # TODO: Fix which files to add
        interface = json.loads(output.stdout)
        instance._method = Method.from_string(interface["method"])
        instance.input = interface["input"]  # TODO: Make python specification
        instance.output = interface["output"]  # TODO: Make python specification

    def solve(self, solver: minizinc.solver.Solver, instance: Instance,
              nr_solutions: Optional[int] = None,
              processes: Optional[int] = None,
              random_seed: Optional[int] = None,
              all_solutions=False,
              free_search: bool = False,
              **kwargs):
        self.analyze(instance)
        with solver.configuration() as conf:
            # Set standard command line arguments
            cmd = [self.executable, "--solver", conf, "--output-mode", "json", "--output-time", "--output-objective"]
            # Enable statistics if possible
            if "-s" in solver.stdFlags:
                cmd.append("-s")

            # Process number of solutions to be generated
            if all_solutions:
                if nr_solutions is not None:
                    raise ValueError("The number of solutions cannot be limited when looking for all solutions")
                if instance.method != Method.SATISFY:
                    raise NotImplementedError("Finding all optimal solutions is not yet implemented")
                if "-a" not in solver.stdFlags:
                    raise NotImplementedError("Solver does not support the -a flag")
                cmd.append("-a")
            elif nr_solutions is not None:
                if nr_solutions <= 0:
                    raise ValueError("The number of solutions can only be set to a positive integer number")
                if instance.method != Method.SATISFY:
                    raise NotImplementedError("Finding all optimal solutions is not yet implemented")
                if "-n" not in solver.stdFlags:
                    raise NotImplementedError("Solver does not support the -n flag")
                cmd.extend(["-n", str(nr_solutions)])
            if "-a" not in solver.stdFlags and instance.method != Method.SATISFY:
                cmd.append("-a")
            # Set number of processes to be used
            if processes is not None:
                if "-p" not in solver.stdFlags:
                    raise NotImplementedError("Solver does not support the -p flag")
                cmd.extend(["-p", str(processes)])
            # Set random seed to be used
            if random_seed is not None:
                if "-r" not in solver.stdFlags:
                    raise NotImplementedError("Solver does not support the -r flag")
                cmd.extend(["-r", str(random_seed)])
            # Enable free search if specified
            if free_search:
                if "-f" not in solver.stdFlags:
                    raise NotImplementedError("Solver does not support the -f flag")
                cmd.append("-f")

            # Add files as last arguments
            cmd.extend(instance.files)
            # Run the MiniZinc process
            output = subprocess.run(cmd, capture_output=True, check=False)
            return Result.from_process(instance, output)

    def version(self) -> tuple:
        output = subprocess.run([self.executable, "--version"], capture_output=True, check=True)
        match = re.search(rb"version (\d+)\.(\d+)\.(\d+)", output.stdout)
        return tuple([int(i) for i in match.groups()])

    def _create_instance(self, model, data=None) -> Instance:
        return Instance(model, data)
