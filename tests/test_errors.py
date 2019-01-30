import pytest
from minizinc.error import ModelAssertionError
from test_case import InstanceTestCase


class AssertionTest(InstanceTestCase):
    code = """
        array [1..10] of int: a = [i | i in 1..10];
        constraint assert(forall (i in 1..9) (a[i] > a[i + 1]), "a not decreasing");
        var 1..10: x;
        constraint a[x] = max(a);
        solve satisfy;
    """

    def test_assert(self):
        with pytest.raises(ModelAssertionError, match='a not decreasing'):
            self.solver.solve(self.instance)
