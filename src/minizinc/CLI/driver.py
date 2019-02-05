import json
import re
import subprocess
import warnings
from datetime import timedelta
from pathlib import Path
from typing import List, Optional, Type

from minizinc import driver

from ..error import parse_error
from ..instance import Method
from ..result import Result
from .instance import CLIInstance
from .solver import CLISolver


def to_python_type(mzn_type: dict) -> Type:
    basetype = mzn_type['type']
    if basetype == 'bool':
        pytype = bool
    elif basetype == 'float':
        pytype = float
    elif basetype == 'int':
        pytype = int
    else:
        warnings.warn("Unable to determine basetype `" + basetype + "` assuming integer type", FutureWarning)
        pytype = int

    dim = mzn_type.get('dim', 0)
    while dim >= 1:
        pytype = List[pytype]
        dim -= 1
    return pytype


class CLIDriver(driver.Driver):
    # Executable path for MiniZinc
    executable: Path

    def __init__(self, executable: Path):
        self.executable = executable
        # Create dynamic classes with the initialised driver
        self.Instance = type('SpecialisedCLIInstance', (CLIInstance,),
                             {'__init__': lambda myself, files=None: super(type(myself), myself).__init__(files, self)})
        self.Solver = type('SpecialisedCLISolver', (CLISolver,), {
                               '__init__': lambda myself, name, version, executable:
                               super(type(myself), myself).__init__(name, version, executable, self)
                           })

        super(CLIDriver, self).__init__(executable)

    def load_solver(self, solver: str) -> CLISolver:
        # Find all available solvers
        output = subprocess.run([self.executable, "--solvers-json"], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                check=True)
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
        ret = CLISolver(info["name"], info["version"], info.get("executable", ""), self)

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

    def analyse(self, instance: CLIInstance):
        with instance.files() as files:
            # TODO: Fix which files to add
            output = subprocess.run([self.executable, "--allow-multiple-assignments", "--model-interface-only"] + files,
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if output.returncode != 0:
            raise parse_error(output.stderr)
        interface = json.loads(output.stdout)
        instance._method = Method.from_string(interface["method"])
        instance.input = {}
        for key, value in interface["input"].items():
            instance.input[key] = to_python_type(value)
        instance.output = {}
        for (key, value) in interface["output"].items():
            instance.output[key] = to_python_type(value)

    def solve(self, solver: CLISolver, instance: CLIInstance,
              timeout: Optional[timedelta] = None,
              nr_solutions: Optional[int] = None,
              processes: Optional[int] = None,
              random_seed: Optional[int] = None,
              all_solutions=False,
              free_search: bool = False,
              ignore_errors=False,
              **kwargs):
        with solver.configuration() as conf:
            # Set standard command line arguments
            cmd = [self.executable, "--solver", conf, "--output-mode", "json", "--output-time", "--output-objective",
                   "--allow-multiple-assignments"]
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
            if "-a" in solver.stdFlags and instance.method != Method.SATISFY:
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

            # Set time limit for the MiniZinc solving
            if timeout is not None:
                cmd.extend(["--time-limit", str(int(timeout.total_seconds() * 1000))])

            # Add files as last arguments
            with instance.files() as files:
                cmd.extend(files)
                # Run the MiniZinc process
                output = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
            return Result.from_process(instance, output, ignore_errors)

    def version(self) -> tuple:
        output = subprocess.run([self.executable, "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                check=True)
        return output.stdout.decode()

    def check_version(self):
        output = subprocess.run([self.executable, "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                check=True)
        match = re.search(rb"version (\d+)\.(\d+)\.(\d+)", output.stdout)
        return tuple([int(i) for i in match.groups()]) >= driver.required_version
