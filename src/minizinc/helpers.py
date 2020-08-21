import sys
from dataclasses import asdict, is_dataclass
from datetime import timedelta
from typing import Any, Dict, Optional, Sequence, Union

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
        result.solution if isinstance(result.solution, list) else [result.solution]
    )

    for i in solution_nrs:
        sol = solutions[i]
        if not check_solution(model, sol, result.status, solver):
            return False

    return True


def check_solution(
    model: minizinc.Model,
    solution: Union[DataClass, Dict[str, Any]],
    status: minizinc.Status,
    solver: minizinc.Solver,
) -> bool:
    """Checks a solution for a model using the given solver.

    Check the correctness of the solving process using a (different) solver
    configuration. A new  model instance is created and will be assigned all
    available values from the given solution. The Instance.solve() method is
    then used to ensure that the same solution with the same expected status is
    reached. Note that this method will not check the optimality of a solution.

    Args:
        model (Model): To model for which the solution was provided
        solution (Union[DataClass, Dict[str, Any]]): The solution to be checked
        status (Status): The expected (compatible) MiniZinc status
        solver (Solver): The solver configuration used to check the
            solution.

    Returns:
        bool: True if the given solution are correctly verified.

    """
    instance = minizinc.Instance(solver, model)
    if is_dataclass(solution):
        solution = asdict(solution)

    for k, v in solution.items():
        if k not in ("objective", "__output_item"):
            instance[k] = v
    try:
        check = instance.solve(timeout=timedelta(seconds=5))
        if status == check.status:
            return True
        elif check.status in [
            minizinc.Status.SATISFIED,
            minizinc.Status.OPTIMAL_SOLUTION,
        ] and status in [
            minizinc.Status.SATISFIED,
            minizinc.Status.OPTIMAL_SOLUTION,
            minizinc.Status.ALL_SOLUTIONS,
        ]:
            return True
        else:
            return False
    except minizinc.MiniZincError:
        if status == minizinc.Status.ERROR:
            return True
        return False
