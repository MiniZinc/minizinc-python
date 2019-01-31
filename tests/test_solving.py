from minizinc.instance import Method
from minizinc.result import Status
from test_case import InstanceTestCase


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
        assert result["_objective"] == 25
        assert len(result) == 1

    def test_intermediate(self):
        result = self.solver.solve(self.instance)
        result.access_all = True
        assert len(result) == 21
        assert result[len(result) - 1]["_objective"] == 25


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
