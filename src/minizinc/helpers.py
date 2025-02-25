import sys
from dataclasses import asdict, is_dataclass
from datetime import timedelta
from typing import Any, Dict, Iterable, List, Optional, Sequence, Union

import minizinc

if sys.version_info >= (3, 8):
    from typing import Protocol

    class DataClass(Protocol):
        # Checking for this attribute is currently the most reliable way to
        # ascertain that something is a dataclass
        __dataclass_fields__: Dict

else:
    DataClass = Any


def check_result(
    model: minizinc.Model,
    result: minizinc.Result,
    solver: minizinc.Solver,
    solution_nrs: Optional[Sequence[int]] = None,
) -> bool:
    """Checks a result object for a model using the given solver.

    Check the correctness of the solving process using a (different) solver
    configuration. The solver configuration is now used to confirm is
    assignment of the variables is correct. By default only the last solution
    will be checked. A sequence of solution numbers can be provided to check
    multiple solutions.

    Args:
        model (Model): To model for which the solution was provided
        result (Result): The solution to be checked
        solver (Solver): The solver configuration used to check the
            solutions.
        solution_nrs: The index set of solutions to be checked. (default:
            ``-1``)

    Returns:
        bool: True if the given result object is correctly verified.

    """
    if solution_nrs is None:
        solution_nrs = [-1]

    solutions = (
        result.solution
        if isinstance(result.solution, list)
        else [result.solution]
    )

    for i in solution_nrs:
        sol = solutions[i]
        if not check_solution(model, sol, result.status, solver):
            return False

    return True


class TimeoutError(Exception):
    """Exception raised for timeout errors (UNKNOWN status) when checking solutions"""

    pass


def check_solution(
    model: minizinc.Model,
    solution: Union[DataClass, Dict[str, Any]],
    status: minizinc.Status,
    solver: minizinc.Solver,
    time_limit: Optional[timedelta] = timedelta(seconds=30),
) -> bool:
    """Checks a solution for a model using the given solver.

    Check the correctness of the solving process using a (different) solver
    configuration. A new  model instance is created and will be assigned all
    available values from the given solution. The Instance.solve() method is
    then used to ensure that the same solution with the same expected status is
    reached. Note that this method will not check the optimality of a solution.

    Args:
        model (Model): The model for which the solution was provided.
        solution (Union[DataClass, Dict[str, Any]]): The solution to be checked.
        status (Status): The expected (compatible) MiniZinc status.
        solver (Solver): The solver configuration used to check the
            solution.
        time_limit (Optional(timedelta)): An optional time limit to check the
            solution.

    Returns:
        bool: True if the given solution are correctly verified.

    Raises:
        TimeoutError: the given time limit was exceeded.
    """
    instance = minizinc.Instance(solver, model)
    if is_dataclass(solution):
        solution = asdict(solution)

    assert isinstance(solution, dict)
    for k, v in solution.items():
        if k not in ("objective", "_output_item", "_checker"):
            instance[k] = v
    check = instance.solve(time_limit=time_limit)

    if check.status is minizinc.Status.UNKNOWN:
        raise TimeoutError(
            f"Solution checking failed because the checker exceeded the allotted time limit of {time_limit}"
        )
    elif status == check.status:
        return True
    return check.status in [
        minizinc.Status.SATISFIED,
        minizinc.Status.OPTIMAL_SOLUTION,
    ] and status in [
        minizinc.Status.SATISFIED,
        minizinc.Status.OPTIMAL_SOLUTION,
        minizinc.Status.ALL_SOLUTIONS,
    ]


def _add_diversity_to_opt_model(
    inst: minizinc.Instance,
    obj_annots: Dict[str, Any],
    vars: List[Dict[str, Any]],
    sol_fix: Optional[Dict[str, Iterable]] = None,
):
    for var in vars:
        # Current and previous variables
        varname = var["name"]
        varprevname = var["prev_name"]

        # Add the 'previous solution variables'
        inst[varprevname] = []

        # Fix the solution to given once
        if sol_fix is not None:
            inst.add_string(
                f"constraint {varname} == {list(sol_fix[varname])};\n"
            )

    # Add the optimal objective.
    if obj_annots["sense"] != "0":
        obj_type = obj_annots["type"]
        inst.add_string(f"{obj_type}: div_orig_opt_objective :: output;\n")
        inst.add_string(
            f"constraint div_orig_opt_objective == {obj_annots['name']};\n"
        )
        if obj_annots["sense"] == "-1":
            inst.add_string(f"solve minimize {obj_annots['name']};\n")
        else:
            inst.add_string(f"solve maximize {obj_annots['name']};\n")
    else:
        inst.add_string("solve satisfy;\n")

    return inst


def _add_diversity_to_div_model(
    inst: minizinc.Instance,
    vars: List[Dict[str, Any]],
    div_anns: Dict[str, Any],
    gap: Union[int, float],
    sols: Dict[str, Any],
):
    # Add the 'previous solution variables'
    for var in vars:
        # Current and previous variables
        varname = var["name"]
        varprevname = var["prev_name"]
        varprevisfloat = "float" in var["prev_type"]

        distfun = var["distance_function"]
        prevsols = sols[varprevname] + [sols[varname]]
        prevsol = (
            __round_elements(prevsols, 6) if varprevisfloat else prevsols
        )  # float values are rounded to six decimal places to avoid infeasibility due to decimal errors.

        # Add the previous solutions to the model code.
        inst[varprevname] = prevsol

        # Add the diversity distance measurement to the model code.
        dim = __num_dim(prevsols)
        dotdots = ", ".join([".." for _ in range(dim - 1)])
        varprevtype = "float" if "float" in var["prev_type"] else "int"
        inst.add_string(
            f"array [1..{len(prevsol)}] of var {varprevtype}: dist_{varname} :: output = [{distfun}({varname}, {varprevname}[sol,{dotdots}]) | sol in 1..{len(prevsol)}];\n"
        )

        # Add minimum distance to the diversity distance measurement in the model code
        if var["lb"] != "infinity":
            inst.add_string(
                f"constraint forall(sol in 1..{len(prevsol)})( dist_{varname}[sol] >= {var['lb']});"
            )

        # Add maximum distance to the diversity distance measurement in the model code
        if var["ub"] != "infinity":
            inst.add_string(
                f"constraint forall(sol in 1..{len(prevsol)})( dist_{varname}[sol] <= {var['ub']});"
            )

    obj_sense = div_anns["objective"]["sense"]
    aggregator = (
        div_anns["aggregator"] if div_anns["aggregator"] != "" else "sum"
    )
    combinator = (
        div_anns["combinator"] if div_anns["combinator"] != "" else "sum"
    )

    # Add the bound on the objective.
    if obj_sense == "-1":
        inst.add_string(f"constraint div_orig_objective <= {gap};\n")
    elif obj_sense == "1":
        inst.add_string(f"constraint div_orig_objective >= {gap};\n")

    # Add new objective: maximize diversity.
    div_combinator = ", ".join(
        [f"{var['coef']} * dist_{var['name']}[sol]" for var in vars]
    )
    dist_total = f"{aggregator}([{combinator}([{div_combinator}]) | sol in 1..{len(prevsol)}])"
    inst.add_string(f"solve maximize {dist_total};\n")

    return inst


def __num_dim(x: List) -> int:
    i = 1
    while isinstance(x[0], list):
        i += 1
        x = x[0]
    return i


def __round_elements(x: List, p: int) -> List:
    for i in range(len(x)):
        if isinstance(x[i], list):
            x[i] = __round_elements(x[i], p)
        elif isinstance(x[i], float):
            x[i] = round(x[i], p)
    return x
