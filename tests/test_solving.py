#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at http://mozilla.org/MPL/2.0/.

from dataclasses import fields

from support import InstanceTestCase

from minizinc.instance import Method
from minizinc.result import Status


class TestSatisfy(InstanceTestCase):
    code = "var 1..5: x"

    def test_solve(self):
        assert self.instance.method == Method.SATISFY
        result = self.instance.solve()
        assert result.status == Status.SATISFIED
        assert result["x"] in range(1, 5 + 1)

    def test_all_solution(self):
        result = self.instance.solve(all_solutions=True)
        assert result.status == Status.ALL_SOLUTIONS
        assert len(result) == 5
        assert sorted([sol.x for sol in result.solution]) == [
            i for i in range(1, 5 + 1)
        ]

    def test_nr_solutions(self):
        result = self.instance.solve(nr_solutions=3)
        assert result.status == Status.SATISFIED
        assert len(result) == 3
        for sol in result.solution:
            assert sol.x in range(1, 5 + 1)


class TestMaximise(InstanceTestCase):
    code = """
        array[1..5] of var 1..5: x;
        solve ::int_search(x, input_order, indomain_min) maximize sum(x);
    """

    def test_solve(self):
        assert self.instance.method == Method.MAXIMIZE
        result = self.instance.solve()
        assert result.status == Status.OPTIMAL_SOLUTION
        assert result.objective == 25

    def test_intermediate(self):
        result = self.instance.solve(intermediate_solutions=True)
        assert len(result) == 21
        assert result.objective == 25


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
        result = self.instance.solve()
        assert result.status == Status.UNSATISFIABLE

    def test_4(self):
        self.instance["n"] = 4
        assert self.instance.method == Method.SATISFY
        result = self.instance.solve()
        assert result.status == Status.SATISFIED
        assert len(result["q"]) == 4


class CheckEmpty(InstanceTestCase):
    code = """int: x = 5;"""

    def test_empty(self):
        assert self.instance.method == Method.SATISFY
        result = self.instance.solve()
        assert len(fields(result.solution)) == 1  # Contains the output_item
        assert result.status == Status.SATISFIED
