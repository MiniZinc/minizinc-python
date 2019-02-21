#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at http://mozilla.org/MPL/2.0/.

from minizinc import Solver
from minizinc.instance import Method
from minizinc.result import Status
from support import InstanceTestCase


class TestSatisfy(InstanceTestCase):
    code = "var 1..5: x"

    def test_solve(self):
        assert self.instance.method == Method.SATISFY
        result = self.solver.solve(self.instance)
        assert result.status == Status.SATISFIED
        assert result["x"] in range(1, 5 + 1)
        assert len(result) == 1

    def test_all_solution(self):
        result = self.solver.solve(self.instance, all_solutions=True)
        assert result.status == Status.ALL_SOLUTIONS
        assert len(result) == 5
        assert sorted([sol["x"] for sol in result]) == [i for i in range(1, 5 + 1)]

    def test_nr_solutions(self):
        result = self.solver.solve(self.instance, nr_solutions=3)
        assert result.status == Status.SATISFIED
        assert len(result) == 3
        for sol in result:
            assert sol["x"] in range(1, 5 + 1)


class TestMaximise(InstanceTestCase):
    code = """
        array[1..5] of var 1..5: x;
        solve ::int_search(x, input_order, indomain_min) maximize sum(x);
    """

    def test_solve(self):
        assert self.instance.method == Method.MAXIMIZE
        result = self.solver.solve(self.instance)
        assert result.status == Status.OPTIMAL_SOLUTION
        assert result.objective == 25
        assert len(result) == 1

    def test_intermediate(self):
        result = self.solver.solve(self.instance)
        result.access_all = True
        assert len(result) == 21
        assert result[len(result) - 1].objective == 25


class TestParameter(InstanceTestCase):
    code = """
        int: n; % The number of queens.
        array [1..n] of var 1..n: q;

        include "alldifferent.mzn";

        constraint alldifferent(q);
        constraint alldifferent(i in 1..n)(q[i] + i);
        constraint alldifferent(i in 1..n)(q[i] - i);
    """

    def test_2(self):
        self.instance["n"] = 2
        assert self.instance.method == Method.SATISFY
        result = self.solver.solve(self.instance)
        assert result.status == Status.UNSATISFIABLE

    def test_4(self):
        self.instance["n"] = 4
        assert self.instance.method == Method.SATISFY
        result = self.solver.solve(self.instance)
        assert result.status == Status.SATISFIED
        assert len(result["q"]) == 4


class CheckResults(InstanceTestCase):
    code = """
        array[1..2] of var 1..10: x;
        constraint x[1] + 1 = x[2];
    """
    other_solver = Solver.lookup("chuffed")

    def test_correct(self):
        assert self.instance.method == Method.SATISFY
        result = self.solver.solve(self.instance)
        assert result.check(self.other_solver)

    def test_incorrect(self):
        assert self.instance.method == Method.SATISFY
        result = self.solver.solve(self.instance)
        result.access_all = True
        result[0].assignments["x"] = [2, 1]
        assert not result.check(self.other_solver)

    def test_check_all(self):
        assert self.instance.method == Method.SATISFY
        result = self.solver.solve(self.instance, all_solutions=True)
        assert result.check(self.other_solver, range(len(result)))

    def test_check_specific(self):
        assert self.instance.method == Method.SATISFY
        result = self.solver.solve(self.instance, nr_solutions=5)
        assert result.check(self.other_solver, [1, 2])
