#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at http://mozilla.org/MPL/2.0/.
import json
import os
import platform
import shutil
import subprocess
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Union

import numpy as np

from .driver import MAC_LOCATIONS, WIN_LOCATIONS
from .result import Result
from .solver import Solver


class MznAnalyse:
    """Python interface to the mzn-analyse executable

    This tool is used to retrieve information about or transform a MiniZinc
    instance. This is used, for example, to  diverse solutions to the given
    MiniZinc instance using the given solver configuration.
    """

    _executable: Path

    def __init__(self, executable: Path):
        self._executable = executable
        if not self._executable.exists():
            raise ConfigurationError(
                f"No MiniZinc data annotator executable was found at '{self._executable}'."
            )

    @classmethod
    def find(
        cls, path: Optional[List[str]] = None, name: str = "mzn-analyse"
    ) -> Optional["MznAnalyse"]:
        """Finds the mzn-analyse executable on default or specified path.

        The find method will look for the mzn-analyse executable to create an
        interface for MiniZinc Python. If no path is specified, then the paths
        given by the environment variables appended by default locations will be
        tried.

        Args:
            path: List of locations to search. name: Name of the executable.

        Returns:
            Optional[MznAnalyse]: Returns a MznAnalyse object when found or None.
        """

        if path is None:
            path = os.environ.get("PATH", "").split(os.pathsep)
            # Add default MiniZinc locations to the path
            if platform.system() == "Darwin":
                path.extend(MAC_LOCATIONS)
            elif platform.system() == "Windows":
                path.extend(WIN_LOCATIONS)

        # Try to locate the MiniZinc executable
        executable = shutil.which(name, path=os.pathsep.join(path))
        if executable is not None:
            return cls(Path(executable))
        return None

    def run(
        self,
        mzn_files: List[Path],
        backend_solver: str,
        solver_div: Solver,
        total_diverse_solutions: Optional[int] = None,
        reference_solution: Optional[Union[Result, Dict[str, Any]]] = None,
        optimise_diverse_sol: Optional[bool] = True,
    ) -> Iterator[Result]:
        from .instance import Instance
        from .model import Model

        verbose = False  # if enabled, outputs the progress
        path_tool = self._executable

        str_div_mzn = "out.mzn"
        str_div_json = "out.json"

        path_div_mzn = Path(str_div_mzn)
        path_div_json = Path(str_div_json)

        # Do not change the order of the arguments 'inline-includes', 'remove-items:output', 'remove-litter' and 'get-diversity-anns'
        tool_run_cmd: List[Union[str, Path]] = [path_tool]

        tool_run_cmd.extend(mzn_files)
        tool_run_cmd.extend(
            [
                "inline-includes",
                "remove-items:output",
                "remove-anns:mzn_expression_name",
                "remove-litter",
                "get-diversity-anns",
                f"out:{str_div_mzn}",
                f"json_out:{str_div_json}",
            ]
        )

        # Extract the diversity annotations.
        subprocess.run(tool_run_cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE)

        assert path_div_mzn.exists()
        assert path_div_json.exists()

        # Load the base model.
        str_model = path_div_mzn.read_text()
        div_annots = json.loads(path_div_json.read_text())["get-diversity-annotations"]

        # Objective annotations.
        obj_annots = div_annots["objective"]
        variables = div_annots["vars"]

        assert len(variables) > 0, "Distance measure not specified"

        base_m = Model()
        base_m.add_string(str_model)

        inst = Instance(solver_div, base_m)

        # Place holder for max gap.
        max_gap = None

        # Place holder for prev solutions
        prev_solutions = None

        # Number of total diverse solutions - If not provided use the count provided in the MiniZinc model
        div_num = (
            int(div_annots["k"])
            if total_diverse_solutions is None
            else total_diverse_solutions
        )
        # Increase the solution count by one if a reference solution is provided
        if reference_solution:
            div_num += 1

        for i in range(1, div_num + 1):
            with inst.branch() as child:
                if i == 1:
                    # Add constraints to the model that sets the decision variables to the reference solution, if provided
                    if reference_solution:
                        if isinstance(reference_solution, Result) and is_dataclass(
                            reference_solution.solution
                        ):
                            solution_obj = asdict(reference_solution.solution)
                        else:
                            assert isinstance(reference_solution, dict)
                            solution_obj = reference_solution
                        for k, v in solution_obj.items():
                            if k not in ("objective", "_output_item", "_checker"):
                                child[k] = v

                    # We will extend the annotated model with the objective and vars.
                    child.add_string(add_diversity_to_opt_model(obj_annots, variables))

                    # Solve original model to optimality.
                    if verbose:
                        model_type = "opt" if obj_annots["sense"] != "0" else "sat"
                        print(
                            f"[Sol 1] Solving the original ({model_type}) model to get a solution"
                        )
                    # inst = minizinc.Instance(solver_div, base_m)
                    res: Result = child.solve()

                    # Ensure that the solution exists.
                    assert res.solution is not None

                    if reference_solution is None:
                        yield res

                    # Calculate max gap.
                    max_gap = (
                        (1 - int(obj_annots["sense"]) * float(div_annots["gap"]))
                        * float(res["div_orig_opt_objective"])
                        if obj_annots["sense"] != "0"
                        else 0
                    )

                    # Store current solution as previous solution
                    prev_solutions = asdict(res.solution)

                else:
                    if verbose:
                        print(
                            f"[Sol {i+1}] Generating diverse solution {i}"
                            + (" (optimal)" if optimise_diverse_sol else "")
                        )

                    # We will extend the annotated model with the objective and vars.
                    child.add_string(
                        add_diversity_to_div_model(
                            variables, obj_annots["sense"], max_gap, prev_solutions
                        )
                    )

                    # Solve div model to get a diverse solution.
                    res = child.solve()

                    # Ensure that the solution exists.
                    assert res.solution is not None

                    # Solution as dictionary
                    sol_div = asdict(res.solution)

                    # Solve diverse solution to optimality after fixing the diversity vars to the obtained solution
                    if optimise_diverse_sol:
                        # COMMENDTED OUT FOR NOW: Merge the solution values.
                        # sol_dist = dict()
                        # for var in variables:
                        #     distvarname = "dist_"+var["name"]
                        #     sol_dist[distvarname] = (sol_div[distvarname])

                        # Solve opt model after fixing the diversity vars to the obtained solution
                        child_opt = Instance(solver_div, base_m)
                        child_opt.add_string(
                            add_diversity_to_opt_model(obj_annots, variables, sol_div)
                        )

                        # Solve the model
                        res = child_opt.solve()

                        # Ensure that the solution exists.
                        assert res.solution is not None

                        # COMMENDTED OUT FOR NOW: Add distance to previous solutions
                        # sol_opt = asdict(res.solution)
                        # sol_opt["distance_to_prev_vars"] = sol_dist

                    yield res

                # Store current solution as previous solution
                curr_solution = asdict(res.solution)
                # Add the current solution to prev solution container
                assert prev_solutions is not None
                for var in variables:
                    prev_solutions[var["prev_name"]].append(curr_solution[var["name"]])


def add_diversity_to_opt_model(obj_annots, vars, sol_fix=None):
    opt_model = ""

    for var in vars:
        # Current and previous variables
        varname = var["name"]
        varprevname = var["prev_name"]

        # Add the 'previous solution variables'
        opt_model += f"{varprevname} = [];\n"

        # Fix the solution to given once
        if sol_fix is not None:
            opt_model += f"constraint {varname} == {list(sol_fix[varname])};\n"

    # Add the optimal objective.
    if obj_annots["sense"] != "0":
        obj_type = obj_annots["type"]
        opt_model += f"{obj_type}: div_orig_opt_objective :: output;\n"
        opt_model += f'constraint div_orig_opt_objective == {obj_annots["name"]};\n'
        if obj_annots["sense"] == "-1":
            opt_model += f'solve minimize {obj_annots["name"]};\n'
        else:
            opt_model += f'solve maximize {obj_annots["name"]};\n'
    else:
        opt_model += "solve satisfy;\n"

    return opt_model


def add_diversity_to_div_model(vars, obj_sense, gap, sols):
    opt_model = ""

    # Indices i,j,k,...
    indices = [chr(ord("i") + x) for x in range(15)]

    # Add the 'previous solution variables'
    for var in vars:
        # Current and previous variables
        varname = var["name"]
        varprevname = var["prev_name"]
        varprevisfloat = "float" in var["prev_type"]

        distfun = var["distance_function"]
        prevsols = np.array(sols[varprevname] + [sols[varname]])
        prevsol = (
            np.round(prevsols, 6) if varprevisfloat else prevsols
        )  # float values are rounded to six decimal places to avoid infeasibility due to decimal errors.

        # Re-derive the domain of the solution from the return variable.
        domains = [f"1..{x}" for x in prevsol.shape]
        domain = ", ".join(domains)
        d = len(domains)

        # Derive the indices for the array reconstruction.
        subindices = ",".join(indices[: (len(domains) - 1)])
        ranger = ", ".join(
            [f"{idx} in {subdomain}" for idx, subdomain in zip(subindices, domains[1:])]
        )

        # Add the previous solutions to the model code.
        opt_model += f"{varprevname} = array{d}d({domain}, {list(prevsol.flat)});\n"

        # Add the diversity distance measurement to the model code.
        varprevtype = "float" if "float" in var["prev_type"] else "int"
        opt_model += (
            f"array [{domains[0]}] of var {varprevtype}: dist_{varname} :: output;\n"
            f"constraint (forall (sol in {domains[0]}) (dist_{varname}[sol] == {distfun}({varname}, [{varprevname}[sol,{subindices}] | {ranger}])));\n"
        )

    # Add the bound on the objective.
    if obj_sense == "-1":
        opt_model += f"constraint div_orig_objective <= {gap};\n"
    elif obj_sense == "1":
        opt_model += f"constraint div_orig_objective >= {gap};\n"

    # Add new objective: maximize diversity.
    dist_sum = "+".join([f'sum(dist_{var["name"]})' for var in vars])
    opt_model += f"solve maximize {dist_sum};\n"

    return opt_model
