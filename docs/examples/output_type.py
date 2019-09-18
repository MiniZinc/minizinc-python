from dataclasses import InitVar, dataclass
from typing import List

from minizinc import Instance, Model, Solver


@dataclass
class TaskAssignment:
    task: List[int]
    objective: int
    __output_item: InitVar[str] = None

    def check(self) -> bool:
        return len(set(self.task)) == len(self.task)


gecode = Solver.lookup("gecode")
model = Model()
model.add_string(
    """
    int: n;
    set of int: DOM = 1..n;
    int: m;
    set of int: COD = 1..m;
    array[DOM,COD] of int: profit;

    array[DOM] of var COD: task;

    include "all_different.mzn";
    constraint all_different(task);

    solve maximize sum(w in DOM)
                (profit[w,task[w]]);
    """
)
model.output_type = TaskAssignment

inst = Instance(gecode, model)
inst["n"] = 4
inst["m"] = 5
inst["profit"] = [[7, 1, 3, 4, 6], [8, 2, 5, 1, 4], [4, 3, 7, 2, 5], [3, 1, 6, 3, 6]]


sol = inst.solve().solution
assert type(sol) == TaskAssignment

if sol.check:
    print("A valid assignment!")
else:
    print("A bad assignment!")
