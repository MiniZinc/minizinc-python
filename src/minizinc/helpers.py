from dataclasses import asdict
from datetime import timedelta
from typing import Optional, Sequence

import minizinc


def check_solution(
    model: minizinc.Model,
    result: minizinc.Result,
    solver: minizinc.Solver,
    solution_nrs: Optional[Sequence[int]] = None,
) -> bool:
    """Checks a solution to for a model using a given solver.

    Check the correctness of the solving process using a (different) solver
    configuration. An instance is branched and will be assigned all
    available values from a solution. The solver configuration is now used
    to confirm is assignment of the variables is correct. By default only
    the last solution will be checked. A sequence of solution numbers can
    be provided to check multiple solutions.

    Args:
        model (Model): To model for which the solution was provided
        result (Result): The solution to be checked
        solver (Solver): The solver configuration used to check the
            solutions.
        solution_nrs: The index set of solutions to be checked. (default:
            ``-1``)

    Returns:
        bool: True if the given solution are correctly verified.

    """
    if solution_nrs is None:
        solution_nrs = [-1]

    instance = minizinc.Instance(solver, model)
    solutions = (
        result.solution if isinstance(result.solution, list) else [result.solution]
    )

    for i in solution_nrs:
        sol = solutions[i]
        with instance.branch() as child:
            for k, v in asdict(sol).items():
                if k not in ("objective", "__output_item"):
                    child[k] = v
            try:
                check = child.solve(timeout=timedelta(seconds=1))
                if result.status != check.status:
                    if check.status in [
                        minizinc.Status.SATISFIED,
                        minizinc.Status.OPTIMAL_SOLUTION,
                    ] and result.status in [
                        minizinc.Status.SATISFIED,
                        minizinc.Status.OPTIMAL_SOLUTION,
                        minizinc.Status.ALL_SOLUTIONS,
                    ]:
                        continue
                    else:
                        return False
            except minizinc.MiniZincError:
                if result.status != minizinc.Status.ERROR:
                    return False

    return True
